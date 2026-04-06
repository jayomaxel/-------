"""
File Purpose:
    Load dataset metadata/CLIP vectors and retrieve top-k similar images for a query vector.

Main Functions:
    - load_dataset_vectors(dataset_key: str = config.DEFAULT_DATASET) -> tuple[np.ndarray, pd.DataFrame]
    - load_retrieval_corpus(dataset_key: str | None = config.RETRIEVAL_DATASET_KEY)
      -> tuple[np.ndarray, pd.DataFrame]
    - retrieve_similar(
        query_vector: np.ndarray,
        dataset_key: str | None = config.RETRIEVAL_DATASET_KEY,
        top_k: int = config.TOP_K_SIMILAR
      ) -> list[dict]

Input / Output Types:
    - Input query vector: np.ndarray, expected shape (512,) or flattenable to 512.
    - Cached dataset vectors: np.ndarray, shape (N, 512), dtype float32/float64.
    - Dataset table: pandas.DataFrame loaded from configured Excel file.
    - Retrieval output: list[dict] with rank/img_name/img_path/similarity/relative_ctr/price.
"""

from pathlib import Path
import functools

import numpy as np
import pandas as pd

import config

DATASET_KEY_COL = "__dataset_key"
DATASET_NAME_COL = "__dataset_name"
IMAGES_DIR_COL = "__images_dir"


def _round4(value: float) -> float:
    """Round a numeric value to 4 decimals and return Python float."""
    rounded = float(np.round(float(value), 4))
    return 0.0 if rounded == 0.0 else rounded


def _resolve_path(path_value: str) -> Path:
    """Resolve a configured relative/absolute path to an absolute Path."""
    path_obj = Path(path_value)
    if path_obj.is_absolute():
        return path_obj
    return (config.ROOT_DIR / path_obj).resolve()


def _get_dataset_config(dataset_key: str) -> dict:
    """Validate dataset key and return configured dataset block."""
    if dataset_key not in config.DATASETS:
        valid_keys = ", ".join(config.DATASETS.keys())
        raise ValueError(
            f"Unknown dataset_key: {dataset_key}. Available dataset keys: {valid_keys}"
        )
    return config.DATASETS[dataset_key]


def _normalize_dataset_keys(dataset_key: str | None) -> tuple[str, ...]:
    """Resolve a retrieval scope into one or more configured dataset keys."""
    if dataset_key is None:
        return tuple(config.DATASETS.keys())

    normalized = str(dataset_key).strip()
    if not normalized or normalized.lower() == "all":
        return tuple(config.DATASETS.keys())

    _get_dataset_config(normalized)
    return (normalized,)


def _safe_float(value: object) -> float:
    """Convert value to float safely; return 0.0 if conversion fails or NaN."""
    try:
        number = float(value)
        if np.isnan(number):
            return 0.0
        return number
    except Exception:
        return 0.0


@functools.lru_cache(maxsize=8)
def load_dataset_vectors(
    dataset_key: str = config.DEFAULT_DATASET,
) -> tuple[np.ndarray, pd.DataFrame]:
    """
    Load dataset Excel rows and precomputed CLIP vectors for a specific dataset key.

    Args:
        dataset_key: Dataset key registered in `config.DATASETS`, for example
            `config.DEFAULT_DATASET` or `"功能性饮料"`.

    Returns:
        tuple[np.ndarray, pd.DataFrame]:
            - vectors: CLIP vector matrix with shape (N, 512)
            - dataframe: dataset rows loaded from configured Excel file

    Raises:
        ValueError: If dataset_key is invalid or vector/dataframe shapes mismatch.
        FileNotFoundError: If configured files are missing. For vector cache miss,
            prompts user to run `precompute_vectors.py`.
        RuntimeError: If file reading fails for other reasons.
    """
    dataset_cfg = _get_dataset_config(dataset_key)

    excel_path = _resolve_path(dataset_cfg["excel_path"])
    vectors_path = _resolve_path(dataset_cfg["cache_vectors"])

    if not vectors_path.exists():
        raise FileNotFoundError(
            f"CLIP vector cache not found: {vectors_path}. "
            "Please run precompute_vectors.py first."
        )

    try:
        dataframe = pd.read_excel(excel_path)
    except FileNotFoundError as exc:
        raise FileNotFoundError(
            f"Excel file not found for dataset '{dataset_key}': {excel_path}"
        ) from exc
    except Exception as exc:
        raise RuntimeError(
            f"Failed to read Excel file for dataset '{dataset_key}': {excel_path}. "
            f"Error: {exc}"
        ) from exc

    try:
        vectors = np.load(vectors_path, allow_pickle=False)
    except FileNotFoundError as exc:
        raise FileNotFoundError(
            f"CLIP vector cache not found: {vectors_path}. "
            "Please run precompute_vectors.py first."
        ) from exc
    except Exception as exc:
        raise RuntimeError(
            f"Failed to load vector cache for dataset '{dataset_key}': {vectors_path}. "
            f"Error: {exc}"
        ) from exc

    if vectors.ndim != 2:
        raise ValueError(
            f"Invalid vector matrix shape for dataset '{dataset_key}': {vectors.shape}. "
            "Expected 2D matrix (N, 512)."
        )
    if vectors.shape[1] != 512:
        raise ValueError(
            f"Invalid vector dimension for dataset '{dataset_key}': {vectors.shape[1]}. "
            "Expected 512."
        )

    if len(dataframe) != vectors.shape[0]:
        raise ValueError(
            f"Row count mismatch for dataset '{dataset_key}': "
            f"Excel rows={len(dataframe)}, vectors rows={vectors.shape[0]}."
        )

    return vectors, dataframe


@functools.lru_cache(maxsize=8)
def _load_retrieval_corpus_cached(
    dataset_keys: tuple[str, ...],
) -> tuple[np.ndarray, pd.DataFrame]:
    """Load and merge one or more configured datasets into a single retrieval corpus."""
    vector_parts: list[np.ndarray] = []
    dataframe_parts: list[pd.DataFrame] = []

    for key in dataset_keys:
        vectors, dataframe = load_dataset_vectors(key)
        dataset_cfg = _get_dataset_config(key)

        dataframe_copy = dataframe.copy()
        dataframe_copy[DATASET_KEY_COL] = key
        dataframe_copy[DATASET_NAME_COL] = str(dataset_cfg.get("display_name", key))
        dataframe_copy[IMAGES_DIR_COL] = str(dataset_cfg["images_dir"])

        vector_parts.append(np.asarray(vectors, dtype=np.float32))
        dataframe_parts.append(dataframe_copy)

    if not vector_parts:
        return np.zeros((0, config.CLIP_DIM), dtype=np.float32), pd.DataFrame()

    merged_vectors = np.concatenate(vector_parts, axis=0)
    merged_dataframe = pd.concat(dataframe_parts, ignore_index=True)
    return merged_vectors, merged_dataframe


def load_retrieval_corpus(
    dataset_key: str | None = config.RETRIEVAL_DATASET_KEY,
) -> tuple[np.ndarray, pd.DataFrame]:
    """
    Load the retrieval corpus for one dataset or the full cross-category corpus.

    Args:
        dataset_key:
            - specific dataset key in `config.DATASETS`
            - `"all"` / `None` to merge all configured datasets

    Returns:
        tuple[np.ndarray, pd.DataFrame]:
            - vectors: CLIP vector matrix with shape (N, 512)
            - dataframe: merged dataset rows enriched with dataset metadata columns
    """
    dataset_keys = _normalize_dataset_keys(dataset_key)
    return _load_retrieval_corpus_cached(dataset_keys)


def retrieve_similar(
    query_vector: np.ndarray,
    dataset_key: str | None = config.RETRIEVAL_DATASET_KEY,
    top_k: int = config.TOP_K_SIMILAR,
) -> list[dict]:
    """
    Retrieve top-k similar items by cosine similarity using vectorized numpy operations.

    Args:
        query_vector: Query CLIP vector, expected shape (512,) or flattenable to 512.
        dataset_key:
            - specific dataset key in `config.DATASETS`
            - `"all"` / `None` to search across all configured datasets
        top_k: Number of top results to return.

    Returns:
        list[dict]: Ranked retrieval results. Each item includes:
            - rank (int)
            - img_name (str, from config.COL_IMG_NAME)
            - img_path (str | None, resolved local path if file exists)
            - similarity (float, 4 decimals)
            - relative_ctr (float, from config.COL_CTR)
            - price (float, from config.COL_PRICE_RAW)

    Raises:
        ValueError: If query vector shape is invalid, norm is zero, or dataset key invalid.
        FileNotFoundError: If required dataset files are missing.
        RuntimeError: If underlying file loading fails.
    """
    vectors, dataframe = load_retrieval_corpus(dataset_key)

    query = np.asarray(query_vector, dtype=np.float32).reshape(-1)
    if query.size != vectors.shape[1]:
        raise ValueError(
            f"Query vector length mismatch: got {query.size}, expected {vectors.shape[1]}."
        )

    query_norm = np.linalg.norm(query)
    if query_norm == 0.0:
        raise ValueError("Query vector norm is zero; cannot compute cosine similarity.")

    # Vectorized cosine similarity: sim = (A · B^T) / (||A|| · ||B||)
    dot_values = vectors @ query
    vector_norms = np.linalg.norm(vectors, axis=1)
    denominator = vector_norms * query_norm

    similarities = np.divide(
        dot_values,
        denominator,
        out=np.zeros_like(dot_values, dtype=np.float32),
        where=denominator > 0.0,
    )

    valid_mask = np.isfinite(similarities)
    if config.SIMILARITY_EXCLUDE_EQ:
        valid_mask &= ~np.isclose(similarities, 1.0)

    candidate_indices = np.where(valid_mask)[0]
    if candidate_indices.size == 0:
        return []

    safe_top_k = max(int(top_k), 0)
    if safe_top_k == 0:
        return []

    k = min(safe_top_k, candidate_indices.size)
    candidate_sims = similarities[candidate_indices]

    partition_ids = np.argpartition(-candidate_sims, kth=k - 1)[:k]
    top_indices = candidate_indices[partition_ids]
    top_indices = top_indices[np.argsort(similarities[top_indices])[::-1]]

    results: list[dict] = []

    for rank, idx in enumerate(top_indices, start=1):
        row = dataframe.iloc[idx]
        img_name = str(row.get(config.COL_IMG_NAME, ""))
        row_dataset_key = str(row.get(DATASET_KEY_COL, ""))
        row_dataset_name = str(row.get(DATASET_NAME_COL, row_dataset_key))
        images_dir = _resolve_path(str(row.get(IMAGES_DIR_COL, "")))

        img_path = None
        if img_name:
            candidate_path = (images_dir / img_name).resolve()
            if candidate_path.exists():
                img_path = str(candidate_path)

        results.append(
            {
                "rank": rank,
                "dataset_key": row_dataset_key,
                "dataset_name": row_dataset_name,
                "img_name": img_name,
                "img_path": img_path,
                "similarity": _round4(similarities[idx]),
                "relative_ctr": _safe_float(row.get(config.COL_CTR, 0.0)),
                "price": _safe_float(row.get(config.COL_PRICE_RAW, 0.0)),
            }
        )

    return results
