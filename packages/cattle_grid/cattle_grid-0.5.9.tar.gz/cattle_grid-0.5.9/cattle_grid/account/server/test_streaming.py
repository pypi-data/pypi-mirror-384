import asyncio

from unittest.mock import AsyncMock, MagicMock
from contextlib import asynccontextmanager

import pytest

from cattle_grid.model.account import EventType

from .streaming import get_message_streamer, construct_routing_key


async def test_get_message_streamer():
    broker = MagicMock()

    @asynccontextmanager
    async def connection():
        yield AsyncMock()

    broker._connection = connection()

    streamer = get_message_streamer(AsyncMock(), 0.1)

    result = streamer("account_name", EventType.incoming)

    assert isinstance(result[0], asyncio.Queue)
    assert isinstance(result[1], asyncio.Task)

    try:
        result[1].cancel()
    except Exception:
        ...


@pytest.mark.parametrize(
    "event_type,expected",
    [
        (EventType.incoming, "receive.alice.incoming"),
        (EventType.outgoing, "receive.alice.outgoing"),
        (EventType.error, "error.alice"),
    ],
)
def test_construct_routing_key(event_type, expected):
    result = construct_routing_key("alice", event_type)

    assert result == expected
