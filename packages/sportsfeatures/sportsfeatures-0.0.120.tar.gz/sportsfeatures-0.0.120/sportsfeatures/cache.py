"""Caching functionality for sportsfeatures."""

# pylint: disable=consider-using-enumerate
import hashlib
import os

import pandas as pd
import pytest_is_running
from joblib import Memory  # type: ignore

from . import __VERSION__

_SPORTS_FEATURES_CACHE_FOLDER = ".sportsfeatures_" + __VERSION__
SPORTS_FEATURES_DF_FILENAME = "df.parquet.gzip"
MEMORY = (
    Memory(".sportsfeatures_joblib_cache", verbose=0)
    if not pytest_is_running
    else Memory()
)


def sportsfeatures_cache_folder() -> str:
    """Return a valid cache folder."""
    if not os.path.exists(_SPORTS_FEATURES_CACHE_FOLDER):
        try:
            os.mkdir(_SPORTS_FEATURES_CACHE_FOLDER)
        except FileExistsError:
            pass
    return _SPORTS_FEATURES_CACHE_FOLDER


def _first_difference_position(df1: pd.DataFrame, df2: pd.DataFrame) -> int | None:
    # Align by index and columns to avoid misalignment issues
    df1, df2 = df1.align(df2)
    # Compare element-wise
    try:
        diff = (df1 != df2).values
        # Iterate by row position
        for i in range(len(diff)):
            if diff[i].any():
                if i == 0:
                    return None
                return i
        return len(diff)  # No difference found
    except TypeError:
        return None


def find_best_cache(cache_name: str, df: pd.DataFrame) -> tuple[str | None, int]:
    """Finds the best cached fit."""
    cache_folder = os.path.join(sportsfeatures_cache_folder(), cache_name)
    if not os.path.exists(cache_folder):
        os.mkdir(cache_folder)
    max_idx = -1
    cache_path = None
    for item in os.listdir(cache_folder):
        full_path = os.path.join(cache_folder, item)
        if not os.path.isdir(full_path):
            continue
        pd_file = os.path.join(full_path, SPORTS_FEATURES_DF_FILENAME)
        cached_df = pd.read_parquet(pd_file)
        diff_idx = _first_difference_position(df, cached_df)
        if diff_idx is not None:
            if diff_idx > max_idx:
                max_idx = diff_idx
                cache_path = full_path
    return cache_path, max_idx


def create_cache(cache_name: str, df: pd.DataFrame) -> str:
    """Creates a cache folder and stores the df."""
    df_hash = hashlib.sha256(df.to_csv().encode()).hexdigest()
    cache_folder = os.path.join(sportsfeatures_cache_folder(), cache_name, df_hash)
    os.makedirs(cache_folder, exist_ok=True)
    df.to_parquet(os.path.join(cache_folder, SPORTS_FEATURES_DF_FILENAME))
    return cache_folder
