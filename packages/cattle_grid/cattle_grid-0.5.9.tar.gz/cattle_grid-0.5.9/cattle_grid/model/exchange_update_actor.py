from enum import StrEnum, auto
from typing import Literal
from pydantic import BaseModel, Field


class UpdateActionType(StrEnum):
    """Available actions for updating the actor"""

    add_identifier = auto()
    """Adds a new identifier. The identifier is assumed to already exist."""
    create_identifier = auto()
    """Creates a new identifier. Must be on a domain controlled by cattle_grid and enabled in the account"""
    update_identifier = auto()
    """Updates an identifer"""
    remove_identifier = auto()
    """Removes an identifier"""

    rename = auto()
    """Updates the internal name of the actor"""

    update_property_value = auto()
    """Adds or updates a property value of the actor"""
    remove_property_value = auto()
    """Removes a property value"""

    add_url = auto()
    """Adds an url to the actor profile"""
    remove_url = auto()
    """Removes an url from the actor profile"""


class UpdateIdentifierAction(BaseModel):
    """Used to update an identifier of the actor"""

    action: Literal[
        UpdateActionType.add_identifier,
        UpdateActionType.create_identifier,
        UpdateActionType.update_identifier,
    ]

    identifier: str = Field(
        description="The identifier", examples=["acct:alice@domain.example"]
    )
    primary: bool = Field(
        False,
        description="Set the identifier as the primary one, if the identifier corresponds to an acct-uri this will update the primary identifier",
    )


class RenameActorAction(BaseModel):
    """Update the internal name of the actor"""

    action: Literal[UpdateActionType.rename] = Field(default=UpdateActionType.rename)

    name: str = Field(description="The new name of the actor")


class UpdatePropertyValueAction(BaseModel):
    """Update a property value of the actor"""

    action: Literal[
        UpdateActionType.update_property_value, UpdateActionType.remove_property_value
    ]

    key: str = Field(
        examples=["author"],
        description="The key of the property value to be created, updated, or deleted",
    )
    value: str | None = Field(
        None,
        examples=["Alice"],
        description="The value of the property value",
    )


class UpdateUrlAction(BaseModel):
    action: Literal[UpdateActionType.add_url, UpdateActionType.remove_url]

    url: str = Field(description="The url to add")
    media_type: str | None = Field(
        default=None, description="The media type for the url"
    )
    rel: str | None = Field(default=None, description="The relation to use")


UpdateAction = (
    UpdateIdentifierAction
    | UpdatePropertyValueAction
    | UpdateUrlAction
    | RenameActorAction
)
