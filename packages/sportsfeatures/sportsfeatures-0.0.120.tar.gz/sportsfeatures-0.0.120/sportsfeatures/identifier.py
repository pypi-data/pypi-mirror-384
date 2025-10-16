"""A description of player representation in the dataframe."""

# pylint: disable=too-many-locals
from .bet import Bet
from .entity_type import EntityType
from .news import News


class Identifier:
    """A way to identify an entity."""

    # pylint: disable=too-many-arguments,too-many-positional-arguments,too-few-public-methods,too-many-instance-attributes

    def __init__(
        self,
        entity_type: EntityType,
        column: str,
        feature_columns: list[str],
        column_prefix: str,
        points_column: str | None = None,
        team_identifier_column: str | None = None,
        field_goals_column: str | None = None,
        assists_column: str | None = None,
        field_goals_attempted_column: str | None = None,
        offensive_rebounds_column: str | None = None,
        turnovers_column: str | None = None,
        bets: list[Bet] | None = None,
        latitude_column: str | None = None,
        longitude_column: str | None = None,
        news: list[News] | None = None,
        birth_date_column: str | None = None,
        image_columns: list[str] | None = None,
    ):
        self.entity_type = entity_type
        self.column = column
        self.feature_columns = feature_columns
        self.column_prefix = column_prefix
        self.points_column = points_column
        self.team_identifier_column = team_identifier_column
        self.field_goals_column = field_goals_column
        self.assists_column = assists_column
        self.field_goals_attempted_column = field_goals_attempted_column
        self.offensive_rebounds_column = offensive_rebounds_column
        self.turnovers_column = turnovers_column
        self.bets = bets if bets is not None else []
        self.latitude_column = latitude_column
        self.longitude_column = longitude_column
        self.news = news if news is not None else []
        self.birth_date_column = birth_date_column
        self.image_columns = image_columns if image_columns is not None else []

    @property
    def columns(self) -> list[str]:
        """The columns recognised by the identifier."""
        columns = {self.column}
        columns |= set(self.numeric_action_columns)
        if self.team_identifier_column is not None:
            columns.add(self.team_identifier_column)
        if self.latitude_column is not None:
            columns.add(self.latitude_column)
        if self.longitude_column is not None:
            columns.add(self.longitude_column)
        return list(columns)

    @property
    def numeric_action_columns(self) -> list[str]:
        """The columns representing action in the numeric space."""
        columns = set()
        for feature_column in self.feature_columns:
            columns.add(feature_column)
        if self.points_column is not None:
            columns.add(self.points_column)
        if self.field_goals_column is not None:
            columns.add(self.field_goals_column)
        if self.assists_column is not None:
            columns.add(self.assists_column)
        if self.field_goals_attempted_column is not None:
            columns.add(self.field_goals_attempted_column)
        if self.offensive_rebounds_column is not None:
            columns.add(self.offensive_rebounds_column)
        if self.turnovers_column is not None:
            columns.add(self.turnovers_column)
        return list(columns)
