from contextlib import asynccontextmanager
from typing import Callable
from faststream.rabbit import RabbitBroker, TestRabbitBroker, RabbitQueue

from cattle_grid.dependencies.globals import global_container


from .load import add_routers_to_broker


@asynccontextmanager
async def with_test_broker_for_extension(
    extensions, subscribers: dict[str, Callable] = {}
):
    """Creates a test broker with subscribtions to the routing_keys given in subscriber.

    ```python
    my_mock = AsyncMock()

    async with with_test_broker_for_extension([extension], {
        "routing_key_to_listen_to": my_mock
    })
    ```
    """
    broker = RabbitBroker()

    for routing_key, subscriber in subscribers.items():
        broker.subscriber(
            RabbitQueue(routing_key, routing_key=routing_key),
            exchange=global_container.exchange,
        )(subscriber)

    add_routers_to_broker(broker, extensions)
    async with TestRabbitBroker(broker, with_real=False) as tbr:
        yield tbr
