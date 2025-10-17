from typing import Annotated
from unittest.mock import AsyncMock
from fast_depends import Depends
from faststream.rabbit import RabbitBroker
from faststream.rabbit.testing import TestRabbitBroker

from .internals import CorrelationId


async def test_correlation_id():
    broker = RabbitBroker()

    mock = AsyncMock()

    async def depends_on_correlation_id(correlation_id: CorrelationId):
        await mock(correlation_id)
        return "test"

    @broker.subscriber("test")
    async def my_func(var: Annotated[str, Depends(depends_on_correlation_id)]): ...

    async with TestRabbitBroker(broker) as tbr:
        await tbr.publish({}, "test", correlation_id="corr")

    mock.assert_awaited_once_with("corr")
