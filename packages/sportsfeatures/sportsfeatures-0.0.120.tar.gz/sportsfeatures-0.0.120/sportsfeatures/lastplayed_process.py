"""Process the time delta between the last time played."""

# pylint: disable=duplicate-code,too-many-branches,too-many-locals

import datetime

import pandas as pd
from tqdm import tqdm

from .columns import DELIMITER
from .identifier import Identifier


def lastplayed_process(
    df: pd.DataFrame, identifiers: list[Identifier], dt_column: str
) -> pd.DataFrame:
    """Process a dataframe for last played."""
    tqdm.pandas(desc="Last Played Features")
    last_identifier_dts: dict[str, datetime.datetime | None] = {}
    first_identifier_dts: dict[str, datetime.datetime] = {}
    birth_identifier_dts: dict[str, datetime.datetime] = {}
    df_cols = df.columns.values.tolist()
    df_dict: dict[str, list[float | None]] = {}

    written_columns = set()
    for row in tqdm(
        df.itertuples(name=None), desc="Last Played Processing", total=len(df)
    ):
        row_dict = {x: row[count + 1] for count, x in enumerate(df_cols)}

        dt = row_dict[dt_column]
        for identifier in identifiers:
            if identifier.column not in row_dict:
                continue
            identifier_id = row_dict[identifier.column]
            if identifier_id is None:
                continue
            if not isinstance(identifier_id, str):
                continue

            key = "_".join([str(identifier.entity_type), identifier_id])

            if key not in birth_identifier_dts:
                if identifier.birth_date_column is not None:
                    if identifier.birth_date_column in row_dict:
                        birth_date = row_dict[identifier.birth_date_column]
                        birth_identifier_dts[key] = birth_date

            last_dt = last_identifier_dts.get(key)
            if last_dt is not None and dt is not None:
                col = DELIMITER.join([identifier.column_prefix, "lastplayeddays"])
                if col not in df_dict:
                    df_dict[col] = [None for _ in range(len(df))]
                written_columns.add(col)
                df_dict[col][row[0]] = (dt - last_dt).days
            last_identifier_dts[key] = dt

            first_dt = first_identifier_dts.get(key)
            if first_dt is not None and dt is not None:
                col = DELIMITER.join([identifier.column_prefix, "firstplayeddays"])
                if col not in df_dict:
                    df_dict[col] = [None for _ in range(len(df))]
                written_columns.add(col)
                df_dict[col][row[0]] = (dt - first_dt).days
            elif first_dt is None and dt is not None:
                first_identifier_dts[key] = dt

            birth_dt = birth_identifier_dts.get(key)
            if birth_dt is not None and dt is not None:
                if birth_dt.tzinfo is None and dt.tzinfo is not None:
                    birth_dt = birth_dt.tz_localize(dt.tzinfo)  # type: ignore
                col = DELIMITER.join([identifier.column_prefix, "birthdays"])
                if col not in df_dict:
                    df_dict[col] = [None for _ in range(len(df))]
                written_columns.add(col)
                df_dict[col][row[0]] = (dt - birth_dt).days

    for column in written_columns:
        df.loc[:, column] = df_dict[column]

    return df[sorted(df.columns.values.tolist())]
