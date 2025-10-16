"""An enum containing the different entity types."""

from enum import StrEnum, auto


class EntityType(StrEnum):
    """The type of entity being represented."""

    PLAYER = auto()
    TEAM = auto()
    VENUE = auto()
    COACH = auto()
    OWNER = auto()
