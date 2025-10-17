from faststream.specification import AsyncAPI
from fastapi import FastAPI

from cattle_grid.version import __version__

from .processing import create_processing_router
from .server import router


def get_async_api_schema() -> AsyncAPI:
    """Returns the async api schema for cattle_grid ActivityPub processing"""
    from faststream.rabbit import RabbitBroker

    broker = RabbitBroker()
    broker.include_router(create_processing_router())

    return AsyncAPI(broker)


def get_fastapi_app() -> FastAPI:
    """Returns the fast api app for ActivityPub processing"""

    app = FastAPI(title="cattle_grid ActivityPub routes", version=__version__)
    app.include_router(router)

    return app
