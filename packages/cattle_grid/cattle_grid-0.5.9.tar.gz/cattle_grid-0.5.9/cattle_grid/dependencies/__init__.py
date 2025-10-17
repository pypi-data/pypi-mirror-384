"""Dependencies injected by fast_depends

cattle_grid uses dependencies to manage objects, one needs access to.
This works by declaring them using [fast_depends.Depends][] and then
injecting them using [fast_depends.inject][].

For example if you want to make a webrequest using the
[aiohttp.ClientSession][], you could use

```python
from cattle_grid.dependencies import ClientSession

async def web_request(session: ClientSession):
    response = await session.get("...")
```

This function can then be called via

```python
from fast_depends import inject

await inject(web_request)()
```

This package contains annotations that should be available in all code
using cattle_grid, i.e. extensions. The sub packages contain methods
for more specific use cases.
"""

from dataclasses import dataclass
import json
import aiohttp
import logging

from typing import Annotated, Callable
from dynaconf import Dynaconf
from fast_depends import Depends
from faststream import Context
from faststream.rabbit import RabbitExchange, RabbitBroker

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from .internals import InternalExchange, CorrelationId
from .globals import get_engine, global_container


logger = logging.getLogger(__name__)


async def get_client_session():
    yield global_container.session


ClientSession = Annotated[aiohttp.ClientSession, Depends(get_client_session)]
"""The [aiohttp.ClientSession][] used by the application"""

ActivityExchange = Annotated[RabbitExchange, Depends(global_container.get_exchange)]
"""The activity exchange"""

AccountExchange = Annotated[
    RabbitExchange, Depends(global_container.get_account_exchange)
]
"""The account exchange"""

SqlAsyncEngine = Annotated[AsyncEngine, Depends(get_engine)]
"""Returns the SqlAlchemy AsyncEngine"""


SqlSessionMaker = Annotated[
    Callable[[], AsyncSession], Depends(global_container.get_session_maker)
]


async def with_sql_session(
    sql_session_maker=Depends(global_container.get_session_maker),
):
    async with sql_session_maker() as session:
        yield session


SqlSession = Annotated[AsyncSession, Depends(with_sql_session)]
"""SQL session that does not commit afterwards"""


async def with_session_commit(session: SqlSession):
    yield session
    await session.commit()


CommittingSession = Annotated[AsyncSession, Depends(with_session_commit)]
"""Session that commits the transaction"""

Config = Annotated[Dynaconf, Depends(global_container.get_config)]
"""Returns the configuration"""


class BasePublisherClass:
    async def __call__(self, *args, **kwargs):
        kwargs_updated = {**kwargs}
        kwargs_updated.update(
            dict(exchange=self.exchange, correlation_id=self.correlation_id)
        )
        return await self.broker.publish(*args, **kwargs_updated)


@dataclass
class ActivityExchangePublisherClass(BasePublisherClass):
    correlation_id: CorrelationId
    exchange: ActivityExchange
    broker: RabbitBroker = Context()


@dataclass
class InternalExchangePublisherClass(BasePublisherClass):
    correlation_id: CorrelationId
    exchange: InternalExchange
    broker: RabbitBroker = Context()


@dataclass
class AccountExchangePublisherClass(BasePublisherClass):
    correlation_id: CorrelationId
    exchange: AccountExchange
    broker: RabbitBroker = Context()


@dataclass
class InternalExchangeRequesterClass(BasePublisherClass):
    correlation_id: CorrelationId
    exchange: InternalExchange
    broker: RabbitBroker = Context()

    async def __call__(self, *args, **kwargs):
        kwargs_updated = {**kwargs}
        kwargs_updated.update(
            dict(exchange=self.exchange, correlation_id=self.correlation_id)
        )
        result = await self.broker.request(*args, **kwargs_updated)
        return json.loads(result.body)


AccountExchangePublisher = Annotated[Callable, Depends(AccountExchangePublisherClass)]
"""Publishes a message to the activity exchange"""

InternalExchangePublisher = Annotated[Callable, Depends(InternalExchangePublisherClass)]
"""Publishes a message to the internal exchange"""

InternalExchangeRequester = Annotated[Callable, Depends(InternalExchangeRequesterClass)]
"""Request a message to the internal exchange"""

ActivityExchangePublisher = Annotated[Callable, Depends(ActivityExchangePublisherClass)]
"""Publishes a message to the activity exchange"""
