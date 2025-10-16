"""A description of a news article in the dataframe."""

# pylint: disable=too-many-arguments,too-many-positional-arguments


class News:
    """A way to define a news article."""

    # pylint: disable=too-few-public-methods

    def __init__(
        self,
        title_column: str,
        published_column: str,
        summary_column: str,
        source_column: str,
    ):
        self.title_column = title_column
        self.published_column = published_column
        self.summary_column = summary_column
        self.source_column = source_column
