import logging
from unittest.mock import AsyncMock
import pytest

from fastapi import FastAPI
from fastapi.testclient import TestClient


from cattle_grid.extensions.examples.html_display.storage import (
    publishing_actor_for_actor_id,
)
from cattle_grid.extensions.testing import with_test_broker_for_extension
from cattle_grid.model import ActivityMessage
from cattle_grid.dependencies.globals import global_container
from cattle_grid.testing.fixtures import *  # noqa
from cattle_grid.extensions.util import lifespan_for_sql_alchemy_base_class
from .database import Base
from . import extension


logger = logging.getLogger(__name__)


@pytest.fixture(autouse=True)
async def create_tables(sql_engine_for_tests):
    lifespan = lifespan_for_sql_alchemy_base_class(Base)
    async with lifespan(sql_engine_for_tests):
        yield


@pytest.fixture
def mock_publish_activity():
    return AsyncMock(return_value=None)


@pytest.fixture
def mock_publish_object():
    return AsyncMock(return_value=None)


@pytest.fixture
async def test_broker(mock_publish_activity, mock_publish_object):
    extension.configure({})

    async with with_test_broker_for_extension(
        [extension],
        {
            "publish_activity": mock_publish_activity,
            "publish_object": mock_publish_object,
            "update_actor": AsyncMock(),
        },
    ) as tbr:
        yield tbr


@pytest.fixture
async def published_object(actor_for_test, test_broker, mock_publish_activity):
    obj = {
        "type": "Note",
        "to": ["as:Public"],
        "content": "I <3 milk!",
        "attributedTo": actor_for_test.actor_id,
    }

    await test_broker.publish(
        ActivityMessage(actor=actor_for_test.actor_id, data=obj).model_dump(),
        routing_key="html_display_publish_object",
        exchange=global_container.exchange,
    )

    logger.info("created object")

    mock_publish_activity.assert_awaited_once()

    args = mock_publish_activity.await_args

    activity = args[1]["data"]

    assert activity["type"] == "Create"

    return activity["object"]


@pytest.fixture
def test_client():
    app = FastAPI()
    app.include_router(extension.api_router, prefix="/html_display")

    return TestClient(app)


@pytest.fixture
async def publishing_actor_for_test(sql_session, actor_for_test):
    actor = await publishing_actor_for_actor_id(sql_session, actor_for_test.actor_id)
    await sql_session.commit()
    return actor
