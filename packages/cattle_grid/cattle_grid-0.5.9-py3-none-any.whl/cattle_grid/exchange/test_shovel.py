import pytest

from unittest.mock import AsyncMock
from faststream.rabbit import RabbitBroker, TestRabbitBroker, RabbitQueue

from cattle_grid.model import ActivityMessage
from cattle_grid.activity_pub.actor import create_actor
from cattle_grid.database.activity_pub_actor import Blocking
from cattle_grid.testing.fixtures import *  # noqa
from cattle_grid.dependencies.globals import global_container

from .shovel import should_shovel_activity
from . import create_router


@pytest.fixture
def mock_incoming():
    return AsyncMock(return_value=None)


@pytest.fixture
def mock_outgoing():
    return AsyncMock(return_value=None)


async def fake_transformer(a, **kwargs):
    return a


@pytest.fixture
async def test_broker(mock_incoming, mock_outgoing):
    broker = RabbitBroker()
    broker.include_router(create_router())

    broker.subscriber(
        RabbitQueue("incoming", routing_key="incoming.*"),
        global_container.exchange,
    )(mock_incoming)
    broker.subscriber(
        RabbitQueue("outgoing", routing_key="outgoing.*"),
        global_container.exchange,
    )(mock_outgoing)
    broker.subscriber(
        RabbitQueue("receive", routing_key="receive.#"),
        global_container.account_exchange,
    )(AsyncMock(return_value=None))
    global_container.transformer = fake_transformer

    async with TestRabbitBroker(broker) as tbr:
        yield tbr


async def test_incoming_message(test_broker, mock_incoming, actor_with_account):
    activity_pub = {
        "@context": "https://www.w3.org/ns/activitystreams",
        "id": "http://remote.test/activity_id",
        "type": "Activity",
        "actor": "http://remote.test/actor",
        "to": "http://actor.example",
        "object": "http://actor.example/object",
    }

    activity = ActivityMessage(
        actor=actor_with_account.actor_id,
        data=activity_pub,
    )

    await test_broker.publish(
        activity,
        exchange=global_container.internal_exchange,
        routing_key="incoming.Activity",
    )

    mock_incoming.assert_awaited_once()

    args = mock_incoming.call_args[1]
    result = args["data"]

    assert result["raw"]["@context"] == activity_pub["@context"]


async def test_incoming_block(test_broker, mock_incoming, actor_with_account):
    activity_pub = {
        "@context": "https://www.w3.org/ns/activitystreams",
        "id": "http://remote.test/activity_id",
        "type": "Block",
        "actor": "http://remote.test/actor",
        "to": "http://actor.example",
        "object": "http://actor.example/object",
    }

    activity = ActivityMessage(actor=actor_with_account.actor_id, data=activity_pub)

    await test_broker.publish(
        activity,
        exchange=global_container.internal_exchange,
        routing_key="incoming.Activity",
    )

    mock_incoming.assert_not_awaited()


async def test_incoming_from_blocked_user(
    test_broker, mock_incoming, sql_session, actor_with_account
):
    remote_actor = "http://remote.test/actor"

    sql_session.add(
        Blocking(
            actor=actor_with_account,
            blocking=remote_actor,
            request="http://blocked.test/id",
            active=True,
        )
    )
    await sql_session.commit()

    activity_pub = {
        "@context": "https://www.w3.org/ns/activitystreams",
        "id": "http://remote.test/activity_id",
        "type": "Activity",
        "actor": remote_actor,
        "to": "http://actor.example",
        "object": "http://actor.example/object",
    }

    activity = ActivityMessage(
        actor=actor_with_account.actor_id,
        data=activity_pub,
    )

    await test_broker.publish(
        activity,
        exchange=global_container.internal_exchange,
        routing_key="incoming.Activity",
    )
    mock_incoming.assert_not_awaited()


async def test_incoming_from_blocked_user_inactive_block(
    test_broker, mock_incoming, sql_session, actor_with_account
):
    remote_actor = "http://remote.test/actor"

    sql_session.add(
        Blocking(
            actor=actor_with_account,
            blocking=remote_actor,
            request="http://blocked.test/id",
            active=False,
        )
    )
    await sql_session.commit()

    activity_pub = {
        "@context": "https://www.w3.org/ns/activitystreams",
        "id": "http://remote.test/activity_id",
        "type": "Activity",
        "actor": remote_actor,
        "to": "http://actor.example",
        "object": "http://actor.example/object",
    }

    activity = ActivityMessage(
        actor=actor_with_account.actor_id,
        data=activity_pub,
    )

    await test_broker.publish(
        activity,
        exchange=global_container.internal_exchange,
        routing_key="incoming.Activity",
    )
    mock_incoming.assert_awaited_once()


async def test_incoming_message_non_gateway_actor(
    test_broker, mock_incoming, sql_session
):
    actor = await create_actor(
        sql_session, "http://localhost/", preferred_username="bob"
    )
    activity_pub = {
        "@context": "https://www.w3.org/ns/activitystreams",
        "id": "http://remote.test/activity_id",
        "type": "Activity",
        "actor": "http://remote.test/actor",
        "to": "http://actor.example",
        "object": "http://actor.example/object",
    }

    activity = ActivityMessage(
        actor=actor.actor_id,
        data=activity_pub,
    )
    await test_broker.publish(
        activity,
        exchange=global_container.internal_exchange,
        routing_key="incoming.Activity",
    )
    mock_incoming.assert_not_awaited()


@pytest.mark.parametrize(
    "activity, expected",
    [
        (
            {
                "type": "Activity",
            },
            True,
        ),
        (
            {
                "type": "Block",
            },
            False,
        ),
        (
            {"type": "Undo", "object": "http://follow.test/id"},
            True,
        ),
    ],
)
async def test_should_shovel_activity(sql_session, activity, expected):
    result = await should_shovel_activity(sql_session, activity)

    assert result == expected


@pytest.mark.parametrize("active, expected", [(True, False), (False, False)])
async def test_should_shovel_activity_undo(
    sql_session, actor_with_account, active, expected
):
    block_id = "http://block.test/id"
    activity = {"type": "Undo", "object": block_id}

    sql_session.add(
        Blocking(
            actor=actor_with_account,
            blocking="http://remote.test",
            request=block_id,
            active=active,
        )
    )
    await sql_session.commit()

    result = await should_shovel_activity(sql_session, activity)

    assert result == expected
