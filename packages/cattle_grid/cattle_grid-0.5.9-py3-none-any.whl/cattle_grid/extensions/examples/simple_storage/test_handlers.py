import pytest
from unittest.mock import AsyncMock, MagicMock

from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.future import select

from cattle_grid.dependencies.globals import global_container
from cattle_grid.extensions.testing import with_test_broker_for_extension
from cattle_grid.testing.fixtures import *  # noqa
from cattle_grid.extensions.util import lifespan_for_sql_alchemy_base_class

from . import (
    extension,
    simple_storage_publish_activity,
    simple_storage_publish_object,
)
from .message_types import PublishActivity, PublishObject
from .models import StoredActivity, StoredObject, Base

activity_stub = {
    "@context": "https://www.w3.org/ns/activitystreams",
    "type": "AnimalSound",
    "actor": "http://alice.example",
    "to": ["http://bob.example"],
    "content": "moo",
}

object_stub = {
    "@context": "https://www.w3.org/ns/activitystreams",
    "type": "Note",
    "attributedTo": "http://alice.example",
    "to": ["http://bob.example"],
    "content": "moo",
}


@pytest.fixture(autouse=True)
async def sql_engine(sql_engine_for_tests):
    lifespan = lifespan_for_sql_alchemy_base_class(Base)

    async with lifespan(sql_engine_for_tests):
        yield sql_engine_for_tests


@pytest.fixture
async def sql_session(sql_engine):
    async_session = async_sessionmaker(sql_engine, expire_on_commit=False)
    yield async_session()


@pytest.fixture
async def send_message_mock():
    yield AsyncMock(return_value=None)


@pytest.fixture
async def test_broker(send_message_mock):
    extension.configure({"prefix": "/simple/storage/"})

    async with with_test_broker_for_extension(
        [extension], {"send_message": send_message_mock}
    ) as tbr:
        yield tbr


@pytest.mark.parametrize(
    "actor,activity",
    [
        ("http://bob.example", activity_stub),
        (
            "http://alice.example",
            {**activity_stub, "id": "http://alice.example/activity1"},
        ),
    ],
)
async def test_simple_storage_publish_activity_errors(actor, activity):
    msg = PublishActivity(
        actor=actor,
        data=activity,
    )

    with pytest.raises(ValueError):
        await simple_storage_publish_activity(
            msg, AsyncMock(), MagicMock(), AsyncMock()
        )


async def test_simple_storage_activity(sql_session, test_broker, send_message_mock):
    msg = PublishActivity(actor="http://alice.example", data=activity_stub)

    await test_broker.publish(
        msg, routing_key="publish_activity", exchange=global_container.exchange
    )

    send_message_mock.assert_awaited_once()

    args = send_message_mock.await_args[1]
    result = (await sql_session.scalars(select(StoredActivity))).all()

    assert len(result) == 1
    assert result[0].data.get("id")

    assert args["data"] == result[0].data


@pytest.mark.parametrize(
    "actor,object",
    [
        ("http://bob.example", object_stub),
        (
            "http://alice.example",
            {**object_stub, "id": "http://alice.example/activity1"},
        ),
    ],
)
async def test_simple_storage_publish_object_errors(actor, object):
    msg = PublishObject(
        actor=actor,
        data=object,
    )

    with pytest.raises(ValueError):
        await simple_storage_publish_object(
            msg,
            AsyncMock(),
            MagicMock(),
            factories=AsyncMock(),
            publisher=AsyncMock(),
        )


async def test_simple_storage_object(
    actor_for_test, sql_session, test_broker, send_message_mock
):
    obj = object_stub.copy()
    obj["attributedTo"] = actor_for_test.actor_id
    msg = PublishObject(actor=actor_for_test.actor_id, data=obj)

    await test_broker.publish(
        msg, routing_key="publish_object", exchange=global_container.exchange
    )

    send_message_mock.assert_awaited_once()

    result = (await sql_session.scalars(select(StoredObject))).all()

    assert len(result) == 1

    assert result[0].data.get("id")
