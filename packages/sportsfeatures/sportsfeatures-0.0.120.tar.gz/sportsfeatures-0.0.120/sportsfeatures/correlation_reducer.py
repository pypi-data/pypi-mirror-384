"""Reduce the inputs to make processing more manageable."""

# pylint: disable=too-many-locals,consider-using-enumerate

import json
import logging
import os

import numpy as np
import pandas as pd

from .identifier import Identifier

_CORRELATION_REDUCER_FILE = "sports-features-correlations.json"


def _find_non_categorical_numeric_columns(df: pd.DataFrame) -> list[str]:
    """
    Finds numeric columns in a Pandas DataFrame that are not categorical.

    Args:
        df (pd.DataFrame): The input DataFrame.

    Returns:
        list: A list of column names that are numeric and not categorical.
    """
    numeric_cols = set(df.select_dtypes(include=np.number).columns.tolist())
    categorical_cols = set(df.select_dtypes(include="category").columns.tolist())
    return list(numeric_cols.difference(categorical_cols))


def _get_correlated_features_to_drop_chunked(
    df: pd.DataFrame,
    threshold: float = 0.85,
    chunk_size: int = 10000,
    random_seed: int = 42,
) -> list[str]:
    """
    Chunked correlation feature reducer to control memory usage.
    Applies correlation pruning within chunks, then across surviving features.
    """
    np.random.seed(random_seed)
    sorted_cols = sorted(_find_non_categorical_numeric_columns(df))
    df_numeric = df[sorted_cols].copy()
    junk_value = np.random.uniform(-1e9, 1e9)
    df_numeric = df_numeric.fillna(junk_value).astype(np.float32)

    # First pass: intra-chunk correlation pruning
    survivors = []
    to_drop_total = set()
    for i in range(0, len(sorted_cols), chunk_size):
        chunk_cols = sorted_cols[i : i + chunk_size]
        chunk_df = df_numeric[chunk_cols]
        chunk_corr = np.corrcoef(chunk_df.values, rowvar=False)
        abs_corr = np.abs(chunk_corr)

        to_drop = set()
        for j in range(len(chunk_cols)):
            if chunk_cols[j] in to_drop:
                continue
            for k in range(j + 1, len(chunk_cols)):
                if chunk_cols[k] in to_drop:
                    continue
                if abs_corr[j, k] > threshold:
                    to_drop.add(chunk_cols[k])

        survivors.extend([col for col in chunk_cols if col not in to_drop])
        to_drop_total.update(to_drop)

    # Second pass: global correlation among survivors
    if len(survivors) < 2:
        return sorted(to_drop_total)

    survivors_df = df_numeric[survivors]
    final_corr = np.corrcoef(survivors_df.values, rowvar=False)
    abs_corr = np.abs(final_corr)

    final_drop = set()
    for i in range(len(survivors)):
        if survivors[i] in final_drop:
            continue
        for j in range(i + 1, len(survivors)):
            if survivors[j] in final_drop:
                continue
            if abs_corr[i, j] > threshold:
                final_drop.add(survivors[j])

    to_drop_total.update(final_drop)
    return sorted(to_drop_total)


def correlation_reducer(
    df: pd.DataFrame, identifiers: list[Identifier], threshold: float
) -> pd.DataFrame:
    """Reduce dataframe by determining the correlation of numeric values."""
    feature_cols = set()
    for identifier in identifiers:
        feature_cols |= set(identifier.feature_columns)

    df = df.dropna(axis=1, how="all")
    # current_cols = set(_find_non_categorical_numeric_columns(df))
    drop_cols = set()
    if os.path.exists(_CORRELATION_REDUCER_FILE):
        with open(_CORRELATION_REDUCER_FILE, encoding="utf8") as handle:
            drop_cols = set(json.load(handle))
    else:
        drop_cols = set(
            _get_correlated_features_to_drop_chunked(df, threshold=threshold)
        )
        drop_cols &= feature_cols
        with open(_CORRELATION_REDUCER_FILE, "w", encoding="utf8") as handle:
            json.dump(list(drop_cols), handle)
    logging.info("Dropped %d columns", len(drop_cols))
    df = df.drop(columns=list(drop_cols))
    return df
