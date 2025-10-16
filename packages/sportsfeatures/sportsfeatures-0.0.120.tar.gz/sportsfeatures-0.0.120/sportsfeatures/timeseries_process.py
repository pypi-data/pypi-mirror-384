"""Processing for time series features."""

# pylint: disable=duplicate-code,too-many-branches,too-many-nested-blocks,too-many-locals,redefined-outer-name,reimported,import-outside-toplevel

import datetime
import os
import tempfile
from warnings import simplefilter

import pandas as pd
from joblib import Parallel, delayed  # type: ignore
from timeseriesfeatures.feature import FEATURE_TYPE_LAG  # type: ignore
from timeseriesfeatures.feature import (FEATURE_TYPE_ROLLING, VALUE_TYPE_DAYS,
                                        VALUE_TYPE_NONE, Feature)
from timeseriesfeatures.transform import Transform  # type: ignore
from tqdm import tqdm

from .columns import DELIMITER
from .entity_type import EntityType
from .identifier import Identifier
from .null_check import is_null

_COLUMN_PREFIX_COLUMN = "_column_prefix"


def _pool_process(
    parquet_file: str,
    features: list[Feature],
    dt_column: str,
) -> None:
    from warnings import simplefilter

    import pandas as pd
    from timeseriesfeatures.process import process  # type: ignore

    simplefilter(action="ignore", category=pd.errors.PerformanceWarning)
    df = pd.read_parquet(parquet_file)
    original_identifier_df = df.copy()
    drop_columns = df.columns.values.tolist()
    if "" in drop_columns:
        drop_columns.remove("")
    drop_columns.remove("_column_prefix")
    df = process(df, features=features, on=dt_column).drop(columns=drop_columns)
    df["_column_prefix"] = original_identifier_df["_column_prefix"]
    df.to_parquet(parquet_file)


def _extract_identifier_timeseries(
    df: pd.DataFrame, identifiers: list[Identifier], dt_column: str, tmpdir: str
) -> None:
    tqdm.pandas(desc="Timeseries Progress")
    identifier_ts: dict[str, pd.DataFrame] = {}
    team_identifiers = [x for x in identifiers if x.entity_type == EntityType.TEAM]
    player_identifiers = [x for x in identifiers if x.entity_type == EntityType.PLAYER]
    relevant_identifiers = team_identifiers + player_identifiers
    df_cols = df.columns.values.tolist()

    for row in tqdm(
        df.itertuples(name=None), desc="Timeseries Progress", total=len(df)
    ):
        row_dict = {x: row[count + 1] for count, x in enumerate(df_cols)}
        for identifier in relevant_identifiers:
            if identifier.column not in row_dict:
                continue
            identifier_id = row_dict[identifier.column]
            if is_null(identifier_id):
                continue
            key = DELIMITER.join([identifier.entity_type, identifier_id])
            identifier_df = identifier_ts.get(key, pd.DataFrame())
            identifier_df.loc[row[0], _COLUMN_PREFIX_COLUMN] = (  # type: ignore
                identifier.column_prefix
            )
            identifier_df.loc[row[0], dt_column] = row_dict[dt_column]  # type: ignore
            for feature_column in identifier.numeric_action_columns:
                if feature_column not in row_dict:
                    continue
                value = row_dict[feature_column]
                if is_null(value):
                    continue
                column = feature_column[len(identifier.column_prefix) :]
                if not column:
                    continue
                if column not in identifier_df:
                    identifier_df[column] = None
                identifier_df.loc[row[0], column] = value  # type: ignore
            identifier_ts[key] = identifier_df.infer_objects()

    for k, v in identifier_ts.items():
        v.to_parquet(os.path.join(tmpdir, f"{k}.parquet"))


def _process_identifier_ts(
    windows: list[datetime.timedelta | None],
    dt_column: str,
    use_multiprocessing: bool,
    tmpdir: str,
) -> None:
    features = [
        Feature(
            feature_type=FEATURE_TYPE_LAG,
            columns=[],
            value1=1,
            transform=str(Transform.NONE),
        ),
        Feature(
            feature_type=FEATURE_TYPE_LAG,
            columns=[],
            value1=2,
            transform=str(Transform.NONE),
        ),
        Feature(
            feature_type=FEATURE_TYPE_LAG,
            columns=[],
            value1=4,
            transform=str(Transform.NONE),
        ),
        Feature(
            feature_type=FEATURE_TYPE_LAG,
            columns=[],
            value1=8,
            transform=str(Transform.NONE),
        ),
    ] + [
        Feature(
            feature_type=FEATURE_TYPE_ROLLING,
            columns=[],
            value1=VALUE_TYPE_NONE if x is None else VALUE_TYPE_DAYS,
            value2=None if x is None else x.days,
            transform=str(Transform.NONE),
        )
        for x in windows
    ]
    parquet_files = [
        os.path.join(tmpdir, x) for x in os.listdir(tmpdir) if x.endswith(".parquet")
    ]
    if use_multiprocessing:
        Parallel(n_jobs=-1)(
            delayed(_pool_process)(x, features, dt_column)
            for x in tqdm(parquet_files, desc="Processing time series")
        )
    else:
        for parquet_file in parquet_files:
            _pool_process(parquet_file, features, dt_column)


def _write_ts_features(
    df: pd.DataFrame,
    dt_column: str,
    tmpdir: str,
) -> pd.DataFrame:
    df_dict = {}

    written_columns = set()
    for parquet_file in tqdm(
        [os.path.join(tmpdir, x) for x in os.listdir(tmpdir) if x.endswith(".parquet")],
        desc="Writing Timeseries Features",
    ):
        identifier_df = pd.read_parquet(parquet_file)
        for row in identifier_df.itertuples(name=None):
            row_dict = {
                x: row[count + 1]
                for count, x in enumerate(identifier_df.columns.values.tolist())
            }
            column_prefix = row_dict[_COLUMN_PREFIX_COLUMN]
            for column, value in row_dict.items():
                if column in {_COLUMN_PREFIX_COLUMN, dt_column, ""}:
                    continue
                key = column_prefix + column
                if key not in df_dict:
                    df_dict[key] = [None for _ in range(len(df))]
                df_dict[key][row[0]] = value
                written_columns.add(key)
    for column in written_columns:
        df.loc[:, column] = df_dict[column]

    return df


def timeseries_process(
    df: pd.DataFrame,
    identifiers: list[Identifier],
    windows: list[datetime.timedelta | None],
    dt_column: str,
    use_multiprocessing: bool,
) -> pd.DataFrame:
    """Process a dataframe for its timeseries features."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tqdm.pandas(desc="Progress")
        simplefilter(action="ignore", category=pd.errors.PerformanceWarning)

        # Write the columns to the dataframe ahead of time.
        df[_COLUMN_PREFIX_COLUMN] = None

        _extract_identifier_timeseries(df, identifiers, dt_column, tmpdir)
        _process_identifier_ts(windows, dt_column, use_multiprocessing, tmpdir)
        df = _write_ts_features(df, dt_column, tmpdir)
        return df.drop(columns=[_COLUMN_PREFIX_COLUMN])
