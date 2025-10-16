"""Process a dataframe for its images."""

import pandas as pd
import requests_cache
from imagefeatures.process import process  # type: ignore

from .identifier import Identifier


def image_process(
    df: pd.DataFrame,
    identifiers: list[Identifier],
    session: requests_cache.CachedSession,
) -> pd.DataFrame:
    """Process image features."""
    image_cols: set[str] = set()
    for identifier in identifiers:
        image_cols.update(identifier.image_columns)
    if image_cols:
        df = process(
            df,
            image_cols,
            session,
        )
    return df[sorted(df.columns.values.tolist())]
