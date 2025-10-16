"""The main process function."""

# pylint: disable=too-many-arguments,too-many-positional-arguments,too-many-statements
import datetime
import logging
import time

import pandas as pd
import requests_cache
import tqdm

from .bets_process import bet_process
from .correlation_reducer import correlation_reducer
from .datetime_process import datetime_process
from .datetimesub_process import datetimesub_process
from .distance_process import distance_process
from .identifier import Identifier
from .image_process import image_process
from .lastplayed_process import lastplayed_process
from .margin_process import margin_process
from .news_process import news_process
from .offensive_efficiency_process import offensive_efficiency_process
from .ordinal_process import ordinal_process
from .players_process import players_process
from .remove_process import remove_process
from .skill_process import skill_process
from .timeseries_process import timeseries_process
from .win_process import win_process


def _reduce_memory_usage(df: pd.DataFrame) -> pd.DataFrame:
    for col in tqdm.tqdm(df.columns, desc="Downcasting Columns"):
        if df[col].dtype == "int64":
            df[col] = pd.to_numeric(df[col], downcast="integer")
        elif df[col].dtype == "float64":
            df[col] = pd.to_numeric(df[col], downcast="float")
    return df


def process(
    df: pd.DataFrame,
    dt_column: str,
    identifiers: list[Identifier],
    windows: list[datetime.timedelta | None],
    categorical_features: set[str],
    use_bets_features: bool = True,
    use_news_features: bool = True,
    datetime_columns: set[str] | None = None,
    use_players_feature: bool = False,
    session: requests_cache.CachedSession | None = None,
    use_multiprocessing: bool = True,
    reduce_input: bool = True,
    initial_correlation_threshold: float = 0.8,
) -> pd.DataFrame:
    """Process the dataframe for sports features."""
    if session is None:
        session = requests_cache.CachedSession(
            "imagefeatures",
            expire_after=requests_cache.NEVER_EXPIRE,
            allowable_methods=("GET", "HEAD", "POST"),
            stale_if_error=True,
        )

    if reduce_input:
        df = correlation_reducer(
            df, identifiers, threshold=initial_correlation_threshold
        )

    start_time = time.perf_counter()
    df = skill_process(df, dt_column, identifiers, windows)
    end_time = time.perf_counter()
    logging.info("Skill process time: %.6f", end_time - start_time)

    start_time = time.perf_counter()
    df = offensive_efficiency_process(df, identifiers)
    end_time = time.perf_counter()
    logging.info("Offensive efficiency process time: %.6f", end_time - start_time)

    start_time = time.perf_counter()
    df = margin_process(df, identifiers)
    end_time = time.perf_counter()
    logging.info("Margin process time: %.6f", end_time - start_time)

    start_time = time.perf_counter()
    df = bet_process(df, identifiers, dt_column, use_bets_features)
    end_time = time.perf_counter()
    logging.info("Bet process time: %.6f", end_time - start_time)

    start_time = time.perf_counter()
    df = datetimesub_process(df, dt_column, identifiers, datetime_columns)
    end_time = time.perf_counter()
    logging.info("Datetimesub process time: %.6f", end_time - start_time)

    start_time = time.perf_counter()
    df = win_process(df, identifiers)
    end_time = time.perf_counter()
    logging.info("Win process time: %.6f", end_time - start_time)

    start_time = time.perf_counter()
    df = timeseries_process(df, identifiers, windows, dt_column, use_multiprocessing)
    end_time = time.perf_counter()
    logging.info("Timeseries process time: %.6f", end_time - start_time)

    start_time = time.perf_counter()
    df = datetime_process(df, dt_column, datetime_columns)
    end_time = time.perf_counter()
    logging.info("Datetime process time: %.6f", end_time - start_time)

    start_time = time.perf_counter()
    df = distance_process(df, identifiers)
    end_time = time.perf_counter()
    logging.info("Distance process time: %.6f", end_time - start_time)

    start_time = time.perf_counter()
    df = lastplayed_process(df, identifiers, dt_column)
    end_time = time.perf_counter()
    logging.info("Lastplayed process time: %.6f", end_time - start_time)

    if use_news_features:
        start_time = time.perf_counter()
        df = news_process(df, identifiers)
        end_time = time.perf_counter()
        logging.info("News process time: %.6f", end_time - start_time)

    start_time = time.perf_counter()
    df = image_process(df, identifiers, session)
    end_time = time.perf_counter()
    logging.info("Image process time: %.6f", end_time - start_time)

    start_time = time.perf_counter()
    df = ordinal_process(df, categorical_features)
    end_time = time.perf_counter()
    logging.info("Ordinal process time: %.6f", end_time - start_time)

    start_time = time.perf_counter()
    df = remove_process(df, identifiers)
    end_time = time.perf_counter()
    logging.info("Remove process time: %.6f", end_time - start_time)

    if use_players_feature:
        start_time = time.perf_counter()
        df = players_process(df, identifiers)
        end_time = time.perf_counter()
        logging.info("Players process time: %.6f", end_time - start_time)

    return _reduce_memory_usage(df)
