"""A class for describing a ratings match."""

# pylint: disable=too-few-public-methods

import datetime

from .team import Team


class Match:
    """Store information about a match."""

    def __init__(self, teams: list[Team], dt: datetime.datetime):
        self.teams = teams
        self.dt = dt
