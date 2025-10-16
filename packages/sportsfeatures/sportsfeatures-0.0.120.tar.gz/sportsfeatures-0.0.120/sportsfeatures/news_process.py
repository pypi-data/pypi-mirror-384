"""Process a dataframe for its news information."""

import pandas as pd
from textfeats.process import process  # type: ignore

from .columns import DELIMITER, NEWS_COLUMN
from .identifier import Identifier


def news_process(df: pd.DataFrame, identifiers: list[Identifier]) -> pd.DataFrame:
    """Process news features."""
    pd.options.mode.chained_assignment = None

    for identifier in identifiers:
        summary_cols = [
            x.summary_column
            for x in identifier.news
            if x.summary_column in df.columns.values.tolist()
        ]
        if not summary_cols:
            continue
        news_df = process(df[summary_cols], True, {"injury"})
        news_df = news_df.drop(columns=summary_cols, errors="ignore")
        for col in news_df.columns.values.tolist():
            df[DELIMITER.join([identifier.column_prefix, NEWS_COLUMN, col])] = news_df[
                col
            ]

    return df[sorted(df.columns.values.tolist())]
