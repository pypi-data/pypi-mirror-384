import logging
from typing import List

from fastapi import FastAPI
from faststream.rabbit import RabbitBroker
from contextlib import asynccontextmanager

from cattle_grid.testing.accounts import create_test_accounts

from .activity_pub.server import router as ap_router
from .auth import auth_router

from .config import default_filenames
from .account.server import router as fe_router
from .account.rabbit import rabbit_router
from .extensions.load import add_routes_to_api, lifespan_from_extensions
from .dependencies.globals import global_container

from .exchange.exception import exception_middleware
from .app import init_extensions, add_routers_to_broker

from .version import __version__
from .database import upgrade_sql_alchemy

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


tags_description = [
    {
        "name": "activity_pub",
        "description": "Endpoints used and consumed by other Fediverse applications to communicate through cattle_grid",
    },
    {
        "name": "auth",
        "description": """Authentication endpoints
    
The auth endpoint allows one to check the HTTP Signature
and reject requests with an invalid one, only based on the
headers. This step then occurs before the request is passed
to the application. Furthermore, this behavior can be shared
accross many services.""",
    },
]


def create_app(
    filenames: List[str] = default_filenames, run_migration: bool = True
) -> FastAPI:
    logger.info("Running cattle grid version %s", __version__)

    global_container.load_config(filenames)

    logger.info("Configuration loaded")

    import os

    alembic_config = __file__.replace("__init__.py", "alembic.ini")

    if run_migration:
        os.system(f"python -malembic -c {alembic_config} upgrade head")

    if global_container.config.testing.enable:  # type:ignore
        logger.warning("Running in testing mode")

    extensions = init_extensions(global_container.config)

    @asynccontextmanager
    async def lifespan(app: FastAPI, broker: RabbitBroker | None = None):
        if broker is None:
            broker = global_container.broker

        broker.add_middleware(exception_middleware)

        async with global_container.common_lifecycle(global_container.config):  # type:ignore
            await upgrade_sql_alchemy(global_container.engine)

            async with lifespan_from_extensions(extensions):
                if global_container.config.processor_in_app:
                    add_routers_to_broker(broker, extensions, global_container.config)
                session = global_container.async_session_maker()  # type: ignore
                await create_test_accounts(session)

                if global_container.config.amqp_uri == "amqp://:memory:":
                    logger.warning("Using in memory amqp")
                    from faststream.rabbit import TestRabbitBroker

                    async with TestRabbitBroker(broker) as br:
                        global_container.broker = br
                        yield
                else:
                    await broker.start()

                    yield
                    await broker.stop()

    app = FastAPI(
        lifespan=lifespan,
        title="cattle_grid",
        description="middle ware for the Fediverse",
        version=__version__,
        openapi_tags=tags_description,
    )

    app.include_router(ap_router)
    app.include_router(
        auth_router,
        prefix="/auth",
    )

    app.include_router(fe_router, prefix="/fe")
    app.include_router(rabbit_router)

    add_routes_to_api(app, extensions)

    @app.get("/")
    async def main() -> str:
        return "cattle_grid"

    return app
