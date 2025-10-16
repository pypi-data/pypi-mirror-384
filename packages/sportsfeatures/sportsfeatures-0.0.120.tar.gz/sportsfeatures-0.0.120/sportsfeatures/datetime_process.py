"""Process a dataframe for its datetime information."""

import logging
from warnings import simplefilter

import pandas as pd
from feature_engine.datetime import DatetimeFeatures


def datetime_process(
    df: pd.DataFrame, dt_column: str, datetime_columns: set[str] | None
) -> pd.DataFrame:
    """Process datetime features."""
    simplefilter(action="ignore", category=pd.errors.PerformanceWarning)
    df_cols = set(df.columns.values.tolist())
    cols = [dt_column]
    if datetime_columns is not None:
        cols.extend(datetime_columns)
    for col in cols:
        if col not in df_cols:
            continue
        df[col] = pd.to_datetime(df[col])
    for col in cols:
        if col not in df_cols:
            continue
        try:
            dtf = DatetimeFeatures(
                variables=[col],  # type: ignore
                features_to_extract="all",
                missing_values="ignore",
                drop_original=False,
                utc=True,
            )
            df = dtf.fit_transform(df)
        except ValueError as exc:
            logging.warning(str(exc))
    return df
