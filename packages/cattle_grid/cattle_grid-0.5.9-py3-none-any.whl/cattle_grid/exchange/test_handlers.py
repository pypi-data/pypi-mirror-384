import pytest
from unittest.mock import AsyncMock
from faststream.rabbit import RabbitBroker, TestRabbitBroker, RabbitQueue

from cattle_grid.activity_pub.actor import actor_to_object
from cattle_grid.database.activity_pub_actor import PublicIdentifier

from cattle_grid.dependencies.globals import global_container
from cattle_grid.testing.fixtures import *  # noqa

from cattle_grid.model.exchange import DeleteActorMessage, UpdateActorMessage
from cattle_grid.testing import mocked_config
from cattle_grid.model.exchange_update_actor import (
    UpdateIdentifierAction,
    UpdateActionType,
)
from . import create_router


@pytest.fixture
def mock_store_activity():
    return AsyncMock(return_value=None)


@pytest.fixture
async def test_broker(mock_store_activity):
    broker = RabbitBroker()
    broker.include_router(create_router())

    broker.subscriber(
        RabbitQueue("store_activity", routing_key="store_activity"),
        global_container.internal_exchange,
    )(mock_store_activity)

    async with TestRabbitBroker(broker) as tbr:
        yield tbr


async def test_delete_actor(mock_store_activity, test_broker, actor_for_test):
    await test_broker.publish(
        DeleteActorMessage(actor=actor_for_test.actor_id),
        routing_key="delete_actor",
        exchange=global_container.exchange,
    )

    mock_store_activity.assert_awaited_once()


async def test_update_actor(test_broker, sql_session, actor_for_test):
    new_name = "Alyssa Newton"
    msg = UpdateActorMessage(actor=actor_for_test.actor_id, profile={"name": new_name})

    await test_broker.publish(
        msg,
        routing_key="update_actor",
        exchange=global_container.exchange,
    )

    await sql_session.refresh(actor_for_test, attribute_names=["profile"])

    obj = actor_to_object(actor_for_test)

    assert obj.get("name") == new_name


async def test_update_actor_profile_not_overwritten(
    sql_session, test_broker, actor_for_test
):
    new_name = "Alyssa Newton"
    new_description = "I was originally called Leibnitz. Also I'm a cat."
    msg = UpdateActorMessage(actor=actor_for_test.actor_id, profile={"name": new_name})

    await test_broker.publish(
        msg,
        routing_key="update_actor",
        exchange=global_container.exchange,
    )

    await sql_session.refresh(actor_for_test)

    obj = actor_to_object(actor_for_test)
    assert obj.get("name") == new_name

    msg = UpdateActorMessage(
        actor=actor_for_test.actor_id, profile={"summary": new_description}
    )

    await test_broker.publish(
        msg,
        routing_key="update_actor",
        exchange=global_container.exchange,
    )

    await sql_session.refresh(actor_for_test)

    obj = actor_to_object(actor_for_test)
    assert obj.get("name") == new_name


async def test_create_identifier(sql_session, actor_with_account, test_broker):
    with mocked_config({"frontend": {"base_urls": ["http://localhost"]}}):
        identifier = "acct:new@localhost"
        new_identifier = UpdateIdentifierAction(
            action=UpdateActionType.create_identifier,
            identifier=identifier,
            primary=False,
        )

        msg = UpdateActorMessage(
            actor=actor_with_account.actor_id, actions=[new_identifier]
        )

        await test_broker.publish(
            msg,
            routing_key="update_actor",
            exchange=global_container.exchange,
        )
        await sql_session.refresh(actor_with_account, attribute_names=["identifiers"])

        obj = actor_to_object(actor_with_account)

        assert identifier in obj.get("identifiers", [])


async def test_update_identifier(sql_session, test_broker, actor_for_test):
    identifier = "acct:one@localhost"
    sql_session.add_all(
        [
            PublicIdentifier(
                actor=actor_for_test,
                identifier="acct:two@localhost",
                name="through_exchange",
                preference=1,
            ),
            PublicIdentifier(
                actor=actor_for_test,
                identifier=identifier,
                name="through_exchange",
                preference=0,
            ),
        ]
    )
    await sql_session.commit()
    await sql_session.refresh(actor_for_test, attribute_names=["identifiers"])

    obj = actor_to_object(actor_for_test)

    assert obj["preferredUsername"] == "two"

    update_identifier = UpdateIdentifierAction(
        action=UpdateActionType.update_identifier,
        identifier=identifier,
        primary=True,
    )

    msg = UpdateActorMessage(actor=actor_for_test.actor_id, actions=[update_identifier])

    await test_broker.publish(
        msg,
        routing_key="update_actor",
        exchange=global_container.exchange,
    )

    import asyncio

    await asyncio.sleep(0.0001)

    await sql_session.refresh(actor_for_test, attribute_names=["identifiers"])

    obj = actor_to_object(actor_for_test)

    assert obj["preferredUsername"] == "one"
