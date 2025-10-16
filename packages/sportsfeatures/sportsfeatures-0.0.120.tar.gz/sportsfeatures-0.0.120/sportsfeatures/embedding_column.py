"""Check whether a column is an embedding column."""

from textfeats.columns import EMBEDDING_COLUMN  # type: ignore

from .columns import DELIMITER


def is_embedding_column(col: str) -> bool:
    """Check whether the column is an embedding."""
    col_split = col.split(DELIMITER)
    if len(col_split) < 3:
        return False
    if col_split[-2] != EMBEDDING_COLUMN:
        return False
    if not col_split[-1].isnumeric():
        return False
    return True
