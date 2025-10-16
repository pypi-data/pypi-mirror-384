"""Calculate win features."""

# pylint: disable=too-many-locals,too-many-branches

from warnings import simplefilter

import pandas as pd
import tqdm

from .columns import DELIMITER
from .identifier import Identifier

WINS_COLUMN = "wins"


def win_process(df: pd.DataFrame, identifiers: list[Identifier]) -> pd.DataFrame:
    """Process wins between teams."""
    simplefilter(action="ignore", category=pd.errors.PerformanceWarning)
    df_dict: dict[str, list[float | None]] = {}
    df_cols = df.columns.values.tolist()
    wins_dict: dict[str, float] = {}

    written_columns = set()
    for row in tqdm.tqdm(
        df.itertuples(name=None), desc="Win Processing", total=len(df)
    ):
        row_dict = {x: row[count + 1] for count, x in enumerate(df_cols)}

        # Write lagged data
        for identifier in identifiers:
            identifier_id = row_dict.get(identifier.column)
            if identifier_id is None:
                continue
            key = DELIMITER.join([identifier.entity_type, identifier_id])
            lagged_value = wins_dict.get(key)
            if lagged_value is None:
                continue
            col = DELIMITER.join([identifier.column_prefix, WINS_COLUMN])
            if col not in df_dict:
                df_dict[col] = [None for _ in range(len(df))]
            df_dict[col][row[0]] = lagged_value
            written_columns.add(col)
            del wins_dict[key]

        # Determine max points
        max_points = None
        for identifier in identifiers:
            points_col = identifier.points_column
            if points_col is None:
                continue
            points = row_dict[points_col]
            if points is None:
                continue
            if max_points is None:
                max_points = points
            else:
                max_points = max(max_points, points)

        # Write the next values
        if max_points is not None:
            for identifier in identifiers:
                identifier_id = row_dict.get(identifier.column)
                if identifier_id is None:
                    continue
                key = DELIMITER.join([identifier.entity_type, identifier_id])
                points_col = identifier.points_column
                if points_col is None:
                    continue
                points = row_dict[points_col]
                if points is None:
                    continue
                wins_dict[key] = float(points == max_points)

    for column in written_columns:
        df.loc[:, column] = df_dict[column]

    # Add new feature columns
    for identifier in identifiers:
        col = DELIMITER.join([identifier.column_prefix, WINS_COLUMN])
        if col in written_columns:
            identifier.feature_columns.append(col)

    return df[sorted(df.columns.values.tolist())]
