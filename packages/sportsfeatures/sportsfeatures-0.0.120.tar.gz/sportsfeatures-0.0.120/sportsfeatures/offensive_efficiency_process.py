"""A process function for determing offensive efficiency of entities."""

# pylint: disable=too-many-locals,too-many-branches,too-many-statements
import pandas as pd
from tqdm import tqdm

from .columns import DELIMITER
from .identifier import Identifier
from .null_check import is_null

OFFENSIVE_EFFICIENCY_COLUMN = "offensiveefficiency"


def offensive_efficiency_process(
    df: pd.DataFrame, identifiers: list[Identifier]
) -> pd.DataFrame:
    """Process a dataframe for offensive efficiency."""
    df_dict: dict[str, list[float | None]] = {}
    df_cols = df.columns.values.tolist()

    written_columns = set()
    for row in tqdm(
        df.itertuples(name=None), desc="Offensive Efficiency Processing", total=len(df)
    ):
        row_dict = {x: row[count + 1] for count, x in enumerate(df_cols)}
        for identifier in identifiers:
            if identifier.field_goals_column is None:
                continue
            if identifier.field_goals_column not in row_dict:
                continue
            field_goals_value = row_dict[identifier.field_goals_column]
            if is_null(field_goals_value):
                continue
            field_goals = float(field_goals_value)
            if identifier.assists_column is None:
                continue
            if identifier.assists_column not in row_dict:
                continue
            assists_value = row_dict[identifier.assists_column]
            if is_null(assists_value):
                continue
            assists = float(assists_value)
            if identifier.field_goals_attempted_column is None:
                continue
            if identifier.field_goals_attempted_column not in row_dict:
                continue
            field_goals_attempted_value = row_dict[
                identifier.field_goals_attempted_column
            ]
            if is_null(field_goals_attempted_value):
                continue
            field_goals_attempted = float(field_goals_attempted_value)
            if identifier.offensive_rebounds_column is None:
                continue
            if identifier.offensive_rebounds_column not in row_dict:
                continue
            offensive_rebounds_value = row_dict[identifier.offensive_rebounds_column]
            if is_null(offensive_rebounds_value):
                continue
            offensive_rebounds = float(offensive_rebounds_value)
            if identifier.turnovers_column is None:
                continue
            if identifier.turnovers_column not in row_dict:
                continue
            turnovers_value = row_dict[identifier.turnovers_column]
            if is_null(turnovers_value):
                continue
            turnovers = float(turnovers_value)
            offensive_efficiency_column = DELIMITER.join(
                [identifier.column_prefix, OFFENSIVE_EFFICIENCY_COLUMN]
            )
            if offensive_efficiency_column not in df_dict:
                df_dict[offensive_efficiency_column] = [None for _ in range(len(df))]
            denominator = (
                field_goals_attempted - offensive_rebounds + assists + turnovers
            )
            df_dict[offensive_efficiency_column][row[0]] = (
                (field_goals + assists) / denominator if denominator != 0.0 else 0.0
            )
            written_columns.add(offensive_efficiency_column)

    for column in written_columns:
        df.loc[:, column] = df_dict[column]

    # Add new feature columns
    for identifier in identifiers:
        col = DELIMITER.join([identifier.column_prefix, OFFENSIVE_EFFICIENCY_COLUMN])
        if col in written_columns:
            identifier.feature_columns.append(col)

    return df[sorted(df.columns.values.tolist())]
