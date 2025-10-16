"""A class describing a team in a match."""

# pylint: disable=too-few-public-methods


class Team:
    """Data about a team in a match."""

    def __init__(
        self,
        players: list[str],
        points: float | None,
        identifier: str,
        coaches: list[str],
    ):
        self.players = players
        self.points = points
        self.identifier = identifier
        self.coaches = coaches
