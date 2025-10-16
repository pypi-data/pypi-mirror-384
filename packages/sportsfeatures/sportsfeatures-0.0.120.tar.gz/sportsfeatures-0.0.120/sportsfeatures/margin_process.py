"""Calculate margin features."""

# pylint: disable=too-many-locals,too-many-branches,duplicate-code

import sys
from warnings import simplefilter

import pandas as pd
import tqdm

from .columns import DELIMITER
from .identifier import Identifier


def margin_process(df: pd.DataFrame, identifiers: list[Identifier]) -> pd.DataFrame:
    """Process margins between teams."""
    simplefilter(action="ignore", category=pd.errors.PerformanceWarning)
    df_dict: dict[str, list[float | None]] = {}
    df_cols = df.columns.values.tolist()
    identifiers_ts: dict[str, dict[str, float]] = {}

    written_columns = set()
    for row in tqdm.tqdm(
        df.itertuples(name=None), desc="Margin Processing", total=len(df)
    ):
        row_dict = {x: row[count + 1] for count, x in enumerate(df_cols)}

        # Write lagged data
        for identifier in identifiers:
            identifier_id = row_dict.get(identifier.column)
            if identifier_id is None:
                continue
            key = DELIMITER.join([identifier.entity_type, identifier_id])
            lagged_values = identifiers_ts.get(key)
            if lagged_values is None:
                continue
            for k, v in lagged_values.items():
                col = identifier.column_prefix + k
                if col not in df_dict:
                    df_dict[col] = [None for _ in range(len(df))]
                df_dict[col][row[0]] = v
                written_columns.add(col)
            del identifiers_ts[key]

        # Find maximum value
        entity_dicts: dict[str, dict[str, float]] = {}
        for identifier in identifiers:
            identifier_id = row_dict.get(identifier.column)
            if identifier_id is None:
                continue
            entity_dict = entity_dicts.get(identifier.entity_type, {})
            for column in identifier.numeric_action_columns:
                value = row_dict.get(column)
                if value is None:
                    continue
                feature_column = column[len(identifier.column_prefix) :]
                entity_dict[feature_column] = max(
                    entity_dict.get(feature_column, sys.float_info.min), value
                )
            entity_dicts[identifier.entity_type] = entity_dict

        # Cache lagged data
        for identifier in identifiers:
            identifier_id = row_dict.get(identifier.column)
            if identifier_id is None:
                continue
            feature_dict = entity_dicts[identifier.entity_type]
            key = DELIMITER.join([identifier.entity_type, identifier_id])
            identifier_dict = {}
            for k, max_value in feature_dict.items():
                full_col = identifier.column_prefix + k
                if full_col not in row_dict:
                    continue
                value = row_dict[full_col]
                abs_col = DELIMITER.join([k, "margin", "absolute"])
                rel_col = DELIMITER.join([k, "margin", "relative"])
                identifier_dict[abs_col] = value - max_value
                identifier_dict[rel_col] = value / max_value
            identifiers_ts[key] = identifier_dict

    for column in written_columns:
        df.loc[:, column] = df_dict[column]

    return df[sorted(df.columns.values.tolist())]
