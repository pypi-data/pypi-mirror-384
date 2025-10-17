from fastapi import FastAPI

from faststream.rabbit import RabbitBroker
from faststream.specification import AsyncAPI

from . import Extension
from .load.lifespan import lifespan_for_extension


def async_schema_for_extension(extension: Extension) -> AsyncAPI:
    """Converts the activity router of the extension to
    a [Schema][faststream.asyncapi.schema.Schema].

    this can be converted to a json string via
    `result.to_json()`."""
    broker = RabbitBroker()

    if extension.activity_router:
        broker.include_router(extension.activity_router)

    return AsyncAPI(broker, title=extension.name)


def fastapi_for_extension(
    extension: Extension, include_broker: bool = False
) -> FastAPI:
    """Converts the api router of the extension to a
    [FastAPI][fastapi.FastAPI] app."""

    app = FastAPI(
        title=extension.name,
        description=extension.description or "",
        lifespan=lifespan_for_extension(extension, include_broker=include_broker),
    )

    app.include_router(extension.api_router)
    return app


def openapi_schema_for_extension(extension: Extension) -> dict:
    """Converts the api router of the extension to a
    dictionary containing the openapi schema"""
    app = fastapi_for_extension(extension)

    return app.openapi()
