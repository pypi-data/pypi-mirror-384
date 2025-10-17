import logging
import math
import multiprocessing as mp
import os
from collections.abc import Iterator
from functools import partial
from multiprocessing.shared_memory import SharedMemory

import anndata as ad
import numpy as np
import pandas as pd
import polars as pl
from numba import get_num_threads, get_thread_id, njit, prange
from scipy.sparse import csc_matrix, csr_matrix
from scipy.stats import anderson_ksamp, false_discovery_control, mannwhitneyu, ttest_ind
from tqdm import tqdm

from ._utils import guess_is_log

# Configure logger
tools_logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

use_experimental = (os.getenv("USE_EXPERIMENTAL", "0") == "1") or (
    os.getenv("USE_EXPERIMENTAL", "0") == "true"
)

KNOWN_METRICS = ["wilcoxon", "anderson", "t-test"]


def _build_shared_matrix(
    data: np.ndarray | np.matrix | csr_matrix | csc_matrix,
) -> tuple[SharedMemory, tuple[int, int], np.dtype]:
    """Create a shared memory matrix from a numpy array."""
    if isinstance(data, np.matrix):
        data = np.asarray(data)
    elif isinstance(data, csr_matrix) or isinstance(data, csc_matrix):
        data = data.toarray()

    # data should be a numpy array at this point
    assert isinstance(data, np.ndarray)

    shared_matrix = SharedMemory(create=True, size=data.nbytes)
    matrix = np.ndarray(data.shape, dtype=data.dtype, buffer=shared_matrix.buf)
    matrix[:] = data
    return shared_matrix, data.shape, data.dtype


def _conclude_shared_memory(shared_memory: SharedMemory):
    """Close and unlink a shared memory."""
    shared_memory.close()
    shared_memory.unlink()


def _combinations_generator(
    target_masks: dict[str, np.ndarray],
    var_indices: dict[str, int],
    reference: str,
    target_list: list[str] | np.ndarray,
    feature_list: list[str] | np.ndarray,
) -> Iterator[tuple]:
    """Generate all combinations of target genes and features."""
    for target in target_list:
        for feature in feature_list:
            yield (
                target_masks[target],
                target_masks[reference],
                var_indices[feature],
                target,
                reference,
                feature,
            )


def _batch_generator(
    combinations: Iterator[tuple],
    batch_size: int,
    num_combinations: int,
) -> Iterator[list[tuple]]:
    """Generate batches of combinations."""
    for _i in range(0, num_combinations, batch_size):
        subset = []
        for _ in range(batch_size):
            try:
                subset.append(next(combinations))
            except StopIteration:
                break
        yield subset


def _process_target_batch_shm(
    batch_tasks: list[tuple],
    shm_name: str,
    shape: tuple[int, int],
    dtype: np.dtype,
    metric: str,
    tie_correct: bool = False,
    is_log1p: bool = False,
    exp_post_agg: bool = True,
    clip_value: float | int | None = 20,
    **kwargs,
) -> list[dict[str, float]]:
    """Process a batch of target gene and feature combinations.

    This is the function that is parallelized across multiple workers.

    Arguments
    =========
    batch_tasks: list[tuple]
        List of tuples containing target mask, reference mask, variable index,
        target name, reference name, and variable name.
    shm_name: str
        Name of the shared memory object.
    shape: tuple[int, int]
        Shape of the matrix.
    dtype: np.dtype
        Data type of the matrix.
    metric: str
        Metric to use for processing.
    tie_correct: bool = False
        Whether to correct for ties.
    is_log1p: bool = False
        Whether to apply log1p transformation.
    exp_post_agg: bool = True
        Whether to apply exponential post-aggregation.
    clip_value: float | int | None
        Default clip value used when log-fold-changes would be NaN or Inf.
        Ignore clipping if set to None.
        fold_change = (
            1/default_clip_value
            if fold_change == inf
            else default_clip_value
            if fold_change == 0
            else fold_change
        )
    **kwargs: Additional keyword arguments.
    """
    # Open shared memory once for the batch
    existing_shm = SharedMemory(name=shm_name)
    matrix = np.ndarray(shape=shape, dtype=dtype, buffer=existing_shm.buf)

    results = []
    for (
        target_mask,
        reference_mask,
        var_index,
        target_name,
        reference_name,
        var_name,
    ) in batch_tasks:
        if target_name == reference_name:
            continue

        x_tgt = matrix[target_mask, var_index]
        x_ref = matrix[reference_mask, var_index]

        μ_tgt = _sample_mean(x_tgt, is_log1p=is_log1p, exp_post_agg=exp_post_agg)
        μ_ref = _sample_mean(x_ref, is_log1p=is_log1p, exp_post_agg=exp_post_agg)

        fc = _fold_change(μ_tgt, μ_ref, clip_value=clip_value)
        pcc = _percent_change(μ_tgt, μ_ref)

        (pval, stat) = (1.0, np.nan)  # default output in case of failure
        try:
            match metric:
                case "wilcoxon":
                    if tie_correct:
                        # default mannwhitneyu behavior
                        de_result = mannwhitneyu(
                            x_tgt, x_ref, use_continuity=True, **kwargs
                        )
                    else:
                        # equivalent to `ranksums` behavior when `use_continuity=False` but statistic changes
                        de_result = mannwhitneyu(
                            x_tgt, x_ref, use_continuity=False, **kwargs
                        )
                    pval, stat = (de_result.pvalue, de_result.statistic)
                case "anderson":
                    de_result = anderson_ksamp([x_tgt, x_ref], **kwargs)
                    pval, stat = (de_result.pvalue, de_result.statistic)  # type: ignore (has attributes pvalue and statistic)
                case "t-test":
                    de_result = ttest_ind(x_tgt, x_ref, **kwargs)
                    pval, stat = (de_result.pvalue, de_result.statistic)  # type: ignore (has attributes pvalue and statistic)
                case _:
                    raise KeyError(f"Unknown Metric: {metric}")
        except ValueError:
            """Don't bail on runtime value errors - just use default values"""

        results.append(
            {
                "target": target_name,
                "reference": reference_name,
                "feature": var_name,
                "target_mean": μ_tgt,
                "reference_mean": μ_ref,
                "percent_change": pcc,
                "fold_change": fc,
                "p_value": pval,
                "statistic": stat,
            }
        )

    existing_shm.close()
    return results


def _get_obs_mask(
    adata: ad.AnnData,
    target_name: str,
    variable_name: str = "target_gene",
) -> np.ndarray:
    """Return a boolean mask for a specific target name in the obs variable."""
    return adata.obs[variable_name] == target_name


def _get_var_index(
    adata: ad.AnnData,
    target_gene: str,
) -> int:
    """Return the index of a specific gene in the var variable.

    Raises
    ------
    ValueError
        If the gene is not found in the dataset.
    """
    var_index = np.flatnonzero(adata.var.index == target_gene)
    if len(var_index) == 0:
        raise ValueError(f"Target gene {target_gene} not found in dataset")
    return var_index[0]


def _sample_mean(
    x: np.ndarray,
    is_log1p: bool,
    exp_post_agg: bool,
) -> float:
    """Determine the sample mean of a 1D array.

    Exponenentiates and subtracts one if `is_log1p == True`

    User can decide whether to exponentiate before or after aggregation.
    """
    if is_log1p:
        if exp_post_agg:
            return np.expm1(np.mean(x))
        else:
            return np.expm1(x).mean()
    else:
        return x.mean()


def _fold_change(
    μ_tgt: float,
    μ_ref: float,
    clip_value: float | int | None = 20,
) -> float:
    """Calculate the fold change between two means."""
    # The fold change is infinite so clip to default value
    if μ_ref == 0:
        return np.nan if clip_value is None else clip_value

    # The fold change is zero so clip to 1 / default value
    if μ_tgt == 0:
        return 0 if clip_value is None else 1 / clip_value

    # Return the fold change
    return μ_tgt / μ_ref


def _percent_change(
    μ_tgt: float,
    μ_ref: float,
) -> float:
    """Calculate the percent change between two means."""
    if μ_ref == 0:
        return np.nan
    return (μ_tgt - μ_ref) / μ_ref


def parallel_differential_expression(
    adata: ad.AnnData,
    groups: list[str] | None = None,
    reference: str = "non-targeting",
    groupby_key: str = "target_gene",
    num_workers: int = 1,
    batch_size: int = 100,
    metric: str = "wilcoxon",
    tie_correct: bool = True,
    is_log1p: bool | None = None,
    exp_post_agg: bool = True,
    clip_value: float | int | None = 20.0,
    as_polars: bool = False,
    **kwargs,
) -> pd.DataFrame | pl.DataFrame:
    """Calculate differential expression between groups of cells.

    Parameters
    ----------
    adata: ad.AnnData
        Annotated data matrix containing gene expression data
    groups: list[str], optional
        List of groups to compare, defaults to None which compares all groups
    reference: str, optional
        Reference group to compare against, defaults to "non-targeting"
    groupby_key: str, optional
        Key in `adata.obs` to group by, defaults to "target_gene"
    num_workers: int
        Number of workers to use for parallel processing, defaults to 1
    batch_size: int
        Number of combinations to process in each batch, defaults to 100
    metric: str
        The differential expression metric to use [wilcoxon, anderson, t-test]
    tie_correct: bool
        Whether to perform continuity (tie) correction for wilcoxon ranksum test
    is_log1p: bool, optional
        Specify exactly whether the data is log1p transformed - will use heuristic to check if not provided
        (see `pdex._utils.guess_is_log`).
    exp_post_agg: bool
        Whether to perform exponential post-aggregation for calculating fold change
        (default: perform exponential post-aggregation)
    clip_value: float | int | None
        Value to clip fold change to if it is infinite or NaN (default: 20.0). Set to None to disable clipping.
    as_polars: bool
        return the output dataframe as a polars dataframe
    **kwargs:
        keyword arguments to pass to metric

    Returns
    -------
    pd.DataFrame containing differential expression results for each group and feature
    """
    if metric not in KNOWN_METRICS:
        raise ValueError(f"Unknown metric: {metric} :: Expecting: {KNOWN_METRICS}")

    unique_targets = np.array(adata.obs[groupby_key].unique())
    if groups is not None:
        unique_targets = [
            target
            for target in unique_targets
            if target in groups or target == reference
        ]
    unique_features = np.array(adata.var.index)

    if not is_log1p:
        is_log1p = guess_is_log(adata)
        if is_log1p:
            logger.info("Auto-Detected log1p for dataset.")
        else:
            logger.info("Auto-Detected non-log1p for dataset.")
    logger.info("Log1p status: %s", is_log1p)

    # Precompute the number of combinations and batches
    n_combinations = len(unique_targets) * len(unique_features)
    n_batches = n_combinations // batch_size + 1

    # Precompute masks for each target gene
    logger.info("Precomputing masks for each target gene")
    target_masks = {
        target: _get_obs_mask(
            adata=adata, target_name=target, variable_name=groupby_key
        )
        for target in tqdm(unique_targets, desc="Identifying target masks")
    }

    # Precompute variable index for each feature
    logger.info("Precomputing variable indices for each feature")
    var_indices = {
        feature: idx
        for idx, feature in enumerate(
            tqdm(unique_features, desc="Identifying variable indices")
        )
    }

    # Isolate the data matrix from the AnnData object
    logger.info("Creating shared memory memory matrix for parallel computing")
    (shared_memory, shape, dtype) = _build_shared_matrix(data=adata.X)  # type: ignore
    shm_name = shared_memory.name

    logger.info(f"Creating generator of all combinations: N={n_combinations}")
    combinations = _combinations_generator(
        target_masks=target_masks,
        var_indices=var_indices,
        reference=reference,
        target_list=unique_targets,
        feature_list=unique_features,
    )
    logger.info(f"Creating generator of all batches: N={n_batches}")
    batches = _batch_generator(
        combinations=combinations,
        batch_size=batch_size,
        num_combinations=n_combinations,
    )

    # Partial function for parallel processing
    task_fn = partial(
        _process_target_batch_shm,
        shm_name=shm_name,
        shape=shape,
        dtype=dtype,
        metric=metric,
        tie_correct=tie_correct,
        is_log1p=is_log1p,
        exp_post_agg=exp_post_agg,
        clip_value=clip_value,
        **kwargs,
    )

    logger.info("Initializing parallel processing pool")
    with mp.Pool(num_workers) as pool:
        logger.info("Processing batches")
        batch_results = list(
            tqdm(
                pool.imap(task_fn, batches),
                total=n_batches,
                desc="Processing batches",
            )
        )

    # Flatten results
    logger.info("Flattening results")
    results = [result for batch in batch_results for result in batch]

    # Close shared memory
    logger.info("Closing shared memory pool")
    _conclude_shared_memory(shared_memory)

    dataframe = pd.DataFrame(results)
    dataframe["fdr"] = false_discovery_control(dataframe["p_value"].values, method="bh")

    if as_polars:
        return pl.DataFrame(dataframe)

    return dataframe


def prepare_ranksum_buffers(X_target, X_ref):
    # 1) Precompute per-gene maxima (int64) and global max
    K_cols = np.maximum(X_target.max(axis=0), X_ref.max(axis=0)).astype(np.int64)
    K_max = int(K_cols.max())
    Kp1 = K_max + 1

    # 2) Allocate per-thread buffer pool once (reuse across calls)
    nthreads = get_num_threads()
    pool_cnt = np.zeros((nthreads, Kp1), dtype=np.int64)
    pool_cnt_t = np.zeros((nthreads, Kp1), dtype=np.int64)
    return K_cols, pool_cnt, pool_cnt_t


@njit(parallel=True, fastmath=True)
def ranksum_kernel_with_pool(X_target, X_ref, K_cols, pool_cnt, pool_cnt_t):
    n_t = X_target.shape[0]
    n_r = X_ref.shape[0]
    n_genes = X_target.shape[1]

    p_values = np.empty(n_genes, dtype=np.float64)
    u_stats = np.empty(n_genes, dtype=np.float64)

    for j in prange(n_genes):
        tid = get_thread_id()  # Numba ≥ 0.56
        cnt = pool_cnt[tid]
        cnt_t = pool_cnt_t[tid]

        Kp1_use = int(K_cols[j] + 1)

        # histograms over just the used slice
        for i in range(n_t):
            v = int(X_target[i, j])
            cnt[v] += 1
            cnt_t[v] += 1
        for i in range(n_r):
            v = int(X_ref[i, j])
            cnt[v] += 1

        # scan buckets
        running = 1
        rank_sum_target = 0.0
        tie_sum = 0
        for v in range(Kp1_use):
            c = cnt[v]
            if c > 0:
                avg = running + 0.5 * (c - 1)
                rank_sum_target += cnt_t[v] * avg
                tie_sum += c * (c - 1) * (c + 1)
                running += c

        # U and p
        u = rank_sum_target - 0.5 * n_t * (n_t + 1)
        u_stats[j] = u

        N = n_t + n_r
        if N > 1:
            tie_adj = tie_sum / (N * (N - 1))
            sigma2 = (n_t * n_r) * ((N + 1) - tie_adj) / 12.0
            if sigma2 > 0.0:
                z = (u - 0.5 * n_t * n_r) / math.sqrt(sigma2)
                p_values[j] = math.erfc(abs(z) / math.sqrt(2.0))
            else:
                p_values[j] = 1.0
        else:
            p_values[j] = 1.0

        # clear just the touched slice
        for v in range(Kp1_use):
            cnt[v] = 0
            cnt_t[v] = 0

    return p_values, u_stats


def _vectorized_ranksum_test_numba(X_target, X_ref, cache=None):
    # Optional tiny cache for (K_cols, pool) keyed by array identities/shape
    if cache is None or "prepared" not in cache:
        K_cols, pool_cnt, pool_cnt_t = prepare_ranksum_buffers(X_target, X_ref)
        if cache is not None:
            cache["prepared"] = (K_cols, pool_cnt, pool_cnt_t)
    else:
        K_cols, pool_cnt, pool_cnt_t = cache["prepared"]

    # Ensure contiguity for Numba perf
    Xt = np.ascontiguousarray(X_target)
    Xr = np.ascontiguousarray(X_ref)
    return ranksum_kernel_with_pool(Xt, Xr, K_cols, pool_cnt, pool_cnt_t)


def _process_single_target_vectorized(
    target: str,
    reference: str,
    obs_values: np.ndarray,
    X: np.ndarray,
    X_ref: np.ndarray,
    means_ref: np.ndarray,
    gene_names: np.ndarray,
    is_log1p: bool,
    exp_post_agg: bool,
    clip_value: float | int | None,
) -> list[dict]:
    """Process a single target using vectorized operations."""
    if target == reference:
        return []

    # Get target data
    target_mask = obs_values == target
    X_target = X[target_mask, :]

    # Vectorized means calculation
    if is_log1p:
        if exp_post_agg:
            means_target = np.expm1(np.mean(X_target, axis=0))
        else:
            means_target = np.mean(np.expm1(X_target), axis=0)
    else:
        means_target = np.mean(X_target, axis=0)

    # Vectorized fold change and percent change across all genes at once
    with np.errstate(divide="ignore", invalid="ignore"):
        fc = means_target / means_ref
        pcc = (means_target - means_ref) / means_ref

        if clip_value is not None:
            fc = np.where(means_ref == 0, clip_value, fc)
            fc = np.where(means_target == 0, 1 / clip_value, fc)
        else:
            fc = np.where(means_ref == 0, np.nan, fc)
            fc = np.where(means_target == 0, 0, fc)

        pcc = np.where(means_ref == 0, np.nan, pcc)

    # Statistical tests across all genes simultaneously
    p_values, statistics = _vectorized_ranksum_test_numba(X_target, X_ref)

    # Build results for all genes at once using vectorized operations
    target_results = [
        {
            "target": target,
            "reference": reference,
            "feature": gene_names[i],
            "target_mean": means_target[i],
            "reference_mean": means_ref[i],
            "percent_change": pcc[i],
            "fold_change": fc[i],
            "p_value": p_values[i],
            "statistic": statistics[i],
        }
        for i in range(len(gene_names))
    ]

    return target_results


def parallel_differential_expression_vec(
    adata: ad.AnnData,
    groups: list[str] | None = None,
    reference: str = "non-targeting",
    groupby_key: str = "target_gene",
    num_workers: int = 1,
    metric: str = "wilcoxon",
    is_log1p: bool | None = None,
    exp_post_agg: bool = True,
    clip_value: float | int | None = 20.0,
    as_polars: bool = False,
) -> pd.DataFrame | pl.DataFrame:
    if metric != "wilcoxon":
        raise ValueError("This implementation currently only supports wilcoxon test")

    # Get unique targets efficiently
    obs_values = adata.obs[groupby_key].values
    unique_targets = np.unique(obs_values)  # type: ignore

    if groups is not None:
        mask = np.isin(unique_targets, groups + [reference])
        unique_targets = unique_targets[mask]

    if not is_log1p:
        is_log1p = guess_is_log(adata)

    logger.info(
        f"vectorized processing: {len(unique_targets)} targets, {adata.n_vars} genes"
    )

    # Convert to dense matrix for fastest access
    if hasattr(adata.X, "toarray"):
        X = adata.X.toarray().astype(np.float32)  # type: ignore
    else:
        X = np.asarray(adata.X, dtype=np.float32)

    # Get reference data once
    reference_mask = obs_values == reference
    X_ref = X[reference_mask, :]  # type: ignore

    # Compute reference means once for all genes
    if is_log1p:
        if exp_post_agg:
            means_ref = np.expm1(np.mean(X_ref, axis=0))
        else:
            means_ref = np.mean(np.expm1(X_ref), axis=0)
    else:
        means_ref = np.mean(X_ref, axis=0)

    # Filter out reference target for parallel processing
    targets_to_process = [target for target in unique_targets if target != reference]
    gene_names = adata.var.index.values

    # Process targets sequentially with numba functions
    logger.info(f"Processing {len(targets_to_process)} targets")
    all_results = []
    for target in tqdm(targets_to_process, desc="Processing targets"):
        target_results = _process_single_target_vectorized(
            target=target,
            reference=reference,
            obs_values=obs_values,  # type: ignore
            X=X,
            X_ref=X_ref,
            means_ref=means_ref,
            gene_names=gene_names,  # type: ignore
            is_log1p=is_log1p,
            exp_post_agg=exp_post_agg,
            clip_value=clip_value,
        )
        all_results.extend(target_results)

    # Create dataframe
    dataframe = pd.DataFrame(all_results)
    dataframe["fdr"] = false_discovery_control(dataframe["p_value"].values, method="bh")

    if as_polars:
        return pl.DataFrame(dataframe)

    return dataframe


def parallel_differential_expression_vec_wrapper(
    adata: ad.AnnData,
    groups: list[str] | None = None,
    reference: str = "non-targeting",
    groupby_key: str = "target_gene",
    num_workers: int = 1,
    batch_size: int = 100,
    metric: str = "wilcoxon",
    tie_correct: bool = True,
    is_log1p: bool | None = None,
    exp_post_agg: bool = True,
    clip_value: float | int | None = 20.0,
    as_polars: bool = False,
    **kwargs,
) -> pd.DataFrame | pl.DataFrame:
    return parallel_differential_expression_vec(
        adata=adata,
        groups=groups,
        reference=reference,
        groupby_key=groupby_key,
        metric=metric,
        is_log1p=is_log1p,
        exp_post_agg=exp_post_agg,
        clip_value=clip_value,
        as_polars=as_polars,
    )


if use_experimental:
    logger.warning("Using experimental features")
    parallel_differential_expression = parallel_differential_expression_vec_wrapper
