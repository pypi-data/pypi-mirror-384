"""The process for removing lookahead features."""

import pandas as pd
import tqdm

from .identifier import Identifier


def remove_process(df: pd.DataFrame, identifiers: list[Identifier]) -> pd.DataFrame:
    """Remove the features from the dataframe."""
    drop_columns: set[str] = set()
    for identifier in tqdm.tqdm(identifiers, desc="Removing features"):
        for feature_col in identifier.feature_columns:
            drop_columns.add(feature_col)
        for bet in identifier.bets:
            drop_columns.add(bet.odds_column)
            drop_columns.add(bet.bookie_id_column)
            if bet.dt_column is not None:
                drop_columns.add(bet.dt_column)
            drop_columns.add(bet.bookie_name_column)
            drop_columns.add(bet.canonical_column)
            drop_columns.add(bet.bet_type_column)
        for news in identifier.news:
            drop_columns.add(news.title_column)
            drop_columns.add(news.published_column)
            drop_columns.add(news.summary_column)
            drop_columns.add(news.source_column)
    return df.drop(columns=list(drop_columns), errors="ignore")
