from pydantic import BaseModel, Field


class MethodInformationModel(BaseModel):
    """cattle_grid allows to define methods on the
    exchange through extensions. This class contains
    a description of them"""

    routing_key: str = Field(
        examples=["send_message"],
        description="""Name of the method""",
    )

    module: str = Field(
        examples=["cattle_grid"],
        description="""Module the extension was imported from. This is cattle_grid for build-in methods""",
    )

    description: str | None = Field(
        default=None,
        examples=["Send a message as the actor"],
        description="""Description of the method""",
    )

    replies: bool = Field(
        default=False,
        description="Indicates whether the method will reply on `receive.NAME.response.trigger` to the trigger event",
    )


class AddMethodInformationMessage(BaseModel):
    """Message to add method information through the exchange"""

    method_information: list[MethodInformationModel] = Field(
        description="""List of method information""",
    )
