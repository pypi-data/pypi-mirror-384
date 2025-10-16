"""A processor for subbing any datetimes with the dt column."""

import logging

import pandas as pd
from feature_engine.datetime import DatetimeSubtraction

from .identifier import Identifier


def datetimesub_process(
    df: pd.DataFrame,
    dt_column: str,
    identifiers: list[Identifier],
    datetime_columns: set[str] | None,
) -> pd.DataFrame:
    """Process date time subtractions."""
    identifier_columns = []
    for identifier in identifiers:
        identifier_columns.extend(identifier.columns)
    columns = (
        df.drop(columns=[dt_column])
        .select_dtypes(
            include=["datetime", "datetime64", "datetime64[ns]", "datetimetz"]
        )
        .columns.values.tolist()
    )
    if datetime_columns is not None:
        for column in datetime_columns:
            if column not in columns:
                columns.append(column)
    if columns:
        for column in columns:
            if column not in identifier_columns:
                continue
            try:
                dts = DatetimeSubtraction(variables=[column], reference=[dt_column])  # type: ignore
                df = dts.fit_transform(df)
            except TypeError as exc:
                logging.warning(
                    "Couldn't use datetime subtraction on column %s: %s",
                    column,
                    str(exc),
                )
    return df
