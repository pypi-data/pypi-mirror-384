from enum import StrEnum, auto
from pydantic import Field
from cattle_grid.model.common import WithActor


class NameActorMessage(WithActor):
    """Message for renaming an actor"""

    name: str = Field(description="Name for the actor", examples=["john"])


class ExportTokenResponse(WithActor):
    """Message containing the export information"""

    token: str = Field(description="One time token")
    export_url: str = Field(
        description="Url including the token the export is located at"
    )


class InteractionType(StrEnum):
    replies = auto()
    likes = auto()
    shares = auto()
