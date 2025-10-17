from unittest.mock import AsyncMock
import pytest

from faststream.rabbit import RabbitBroker, TestRabbitBroker, RabbitQueue

from cattle_grid.dependencies.globals import global_container
from cattle_grid.testing.fixtures import *  # noqa

from . import create_processing_router


@pytest.fixture
async def mock_incoming_activity():
    return AsyncMock(return_value=None)


@pytest.fixture
async def mock_to_send():
    return AsyncMock(return_value=None)


@pytest.fixture
async def broker(mock_incoming_activity, mock_to_send):
    br = RabbitBroker("amqp://guest:guest@localhost:5672/")
    br.include_router(create_processing_router())

    br.subscriber(
        RabbitQueue("test_queue", routing_key="to_send"),
        exchange=global_container.internal_exchange,
    )(mock_to_send)

    br.subscriber(
        RabbitQueue("test_queue", routing_key="incoming.Activity"),
        exchange=global_container.internal_exchange,
    )(mock_incoming_activity)

    async with TestRabbitBroker(br, connect_only=False) as tbr:
        yield tbr
