from pydantic import ConfigDict, Field, field_serializer
from typing import Annotated, Dict, Any, List

from .common import WithActor
from .exchange_update_actor import UpdateAction


class UpdateActorMessage(WithActor):
    """
    Allows one to update the actor object
    """

    # model_config = ConfigDict(
    #     extra="forbid",
    # )

    profile: Dict[str, Any] | None = Field(
        default=None,
        examples=[{"summary": "A new description of the actor"}],
        description="""
    New profile object for the actor. The fields.
    """,
    )
    autoFollow: bool | None = Field(
        default=None,
        examples=[True, False, None],
        description="""
    Enables setting actors to automatically accept follow requests
    """,
    )

    actions: List[
        Annotated[
            UpdateAction,
            Field(
                discriminator="action",
            ),
        ]
    ] = Field(
        default_factory=list,
        description="""Actions to be taken when updating the profile""",
    )

    @field_serializer("actions")
    def serialize_dt(self, actions: List[UpdateAction], _info):
        return [action.model_dump() for action in actions]


class DeleteActorMessage(WithActor):
    """
    Allows one to delete the actor object
    """

    model_config = ConfigDict(
        extra="forbid",
    )
