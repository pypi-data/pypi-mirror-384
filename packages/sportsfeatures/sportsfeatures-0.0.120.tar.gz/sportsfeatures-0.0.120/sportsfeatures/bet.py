"""A description of a bet in the dataframe."""
# pylint: disable=too-many-arguments,too-many-positional-arguments


class Bet:
    """A way to define a bet."""

    # pylint: disable=too-few-public-methods

    def __init__(
        self,
        odds_column: str,
        bookie_id_column: str,
        canonical_column: str,
        bookie_name_column: str,
        bet_type_column: str,
        dt_column: str | None = None,
    ):
        self.odds_column = odds_column
        self.bookie_id_column = bookie_id_column
        self.dt_column = dt_column
        self.canonical_column = canonical_column
        self.bookie_name_column = bookie_name_column
        self.bet_type_column = bet_type_column
