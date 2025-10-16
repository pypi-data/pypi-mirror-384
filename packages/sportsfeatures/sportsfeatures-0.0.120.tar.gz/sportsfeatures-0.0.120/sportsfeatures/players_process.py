"""Calculate players features."""

# pylint: disable=too-many-locals,too-many-branches,too-many-statements
from warnings import simplefilter

import pandas as pd
import tqdm
from pandas.api.types import is_float_dtype

from .columns import DELIMITER
from .identifier import Identifier

PLAYERS_COLUMN = "players"


def players_process(df: pd.DataFrame, identifiers: list[Identifier]) -> pd.DataFrame:
    """Process players stats on a team."""
    simplefilter(action="ignore", category=pd.errors.PerformanceWarning)
    df_cols = df.columns.values.tolist()

    team_identifiers: dict[str, list[Identifier]] = {}
    for identifier in identifiers:
        if identifier.team_identifier_column is None:
            continue
        team_identifier = [
            x for x in identifiers if x.column == identifier.team_identifier_column
        ]
        team_identifiers[team_identifier[0].column_prefix] = team_identifiers.get(
            team_identifier[0].column_prefix, []
        ) + [identifier]

    for column_prefix, player_identifiers in tqdm.tqdm(
        team_identifiers.items(), desc="Players Processing"
    ):
        columns: dict[str, list[float]] = {}
        for identifier in player_identifiers:
            for col in df_cols:
                if not col.startswith(identifier.column_prefix):
                    continue
                if not is_float_dtype(df[col]):
                    continue
                key = col[len(identifier.column_prefix) + 1 :]
                current_cols = columns.get(key, [])
                current_cols.append(col)
                columns[key] = current_cols

        for column_key, cols in columns.items():
            if len(cols) < 2:
                continue
            df[DELIMITER.join([column_prefix, PLAYERS_COLUMN, column_key, "mean"])] = (
                df[cols].mean(axis=1)
            )
            df[
                DELIMITER.join([column_prefix, PLAYERS_COLUMN, column_key, "median"])
            ] = df[cols].median(axis=1)
            df[DELIMITER.join([column_prefix, PLAYERS_COLUMN, column_key, "min"])] = df[
                cols
            ].min(axis=1)
            df[DELIMITER.join([column_prefix, PLAYERS_COLUMN, column_key, "max"])] = df[
                cols
            ].max(axis=1)
            df[DELIMITER.join([column_prefix, PLAYERS_COLUMN, column_key, "count"])] = (
                df[cols].notnull().sum(axis=1)
            )
            df[DELIMITER.join([column_prefix, PLAYERS_COLUMN, column_key, "sum"])] = df[
                cols
            ].sum(axis=1)
            df[DELIMITER.join([column_prefix, PLAYERS_COLUMN, column_key, "var"])] = df[
                cols
            ].var(axis=1)
            df[DELIMITER.join([column_prefix, PLAYERS_COLUMN, column_key, "std"])] = df[
                cols
            ].std(axis=1)
            df[DELIMITER.join([column_prefix, PLAYERS_COLUMN, column_key, "skew"])] = (
                df[cols].skew(axis=1)
            )
            df[DELIMITER.join([column_prefix, PLAYERS_COLUMN, column_key, "kurt"])] = (
                df[cols].kurt(axis=1)
            )
            df[DELIMITER.join([column_prefix, PLAYERS_COLUMN, column_key, "sem"])] = df[
                cols
            ].sem(axis=1)

    return df[sorted(df.columns.values.tolist())]
