from enum import StrEnum, auto
from pydantic import BaseModel, Field


class RelationshipStatus(StrEnum):
    """The (technical) states of a relationship (follower, following, blocking)"""

    none = auto()
    accepted = auto()
    waiting = auto()


class Relationship(BaseModel):
    """Description of the relationship of an actor to another one"""

    status: RelationshipStatus = Field(
        description="The current status of the relationship"
    )
    requests: list[str] = Field(
        default=[], description="List of URIs of the involved requests"
    )
