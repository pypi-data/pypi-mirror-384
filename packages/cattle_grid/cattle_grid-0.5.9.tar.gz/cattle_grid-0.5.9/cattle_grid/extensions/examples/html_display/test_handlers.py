from sqlalchemy import select
from cattle_grid.dependencies.globals import global_container
from cattle_grid.extensions.examples.html_display.database import PublishingActor
from cattle_grid.extensions.examples.html_display.types import NameActorMessage
from cattle_grid.manage.actor import ActorManager
from cattle_grid.model import ActivityMessage

from . import extension
from .testing import *  # noqa


async def test_publish_html(
    test_broker, actor_for_test, mock_publish_activity, mock_publish_object
):
    obj = {
        "type": "Note",
        "to": "as:Public",
        "content": "I <3 milk!",
        "attributedTo": actor_for_test.actor_id,
    }

    await test_broker.publish(
        ActivityMessage(actor=actor_for_test.actor_id, data=obj),
        routing_key="html_display_publish_object",
        exchange=global_container.exchange,
    )

    mock_publish_activity.assert_awaited_once()
    mock_publish_object.assert_not_awaited()

    args = mock_publish_activity.await_args

    assert args[1]["actor"] == actor_for_test.actor_id


async def test_publish_html_private(
    test_broker, actor_for_test, mock_publish_activity, mock_publish_object
):
    obj = {
        "type": "Note",
        "to": ["http://remote.example/actor"],
        "content": "I <3 milk!",
        "attributedTo": actor_for_test.actor_id,
    }

    await test_broker.publish(
        ActivityMessage(actor=actor_for_test.actor_id, data=obj),
        routing_key="html_display_publish_object",
        exchange=global_container.exchange,
    )

    mock_publish_activity.assert_not_awaited()
    mock_publish_object.assert_awaited_once()


async def test_rename_actor(test_broker, actor_with_account, sql_session):
    await test_broker.publish(
        NameActorMessage(actor=actor_with_account.actor_id, name="sue"),
        routing_key="html_display_name",
        exchange=global_container.exchange,
    )

    actor = await sql_session.scalar(
        select(PublishingActor).where(
            PublishingActor.actor == actor_with_account.actor_id
        )
    )

    assert actor.name == "sue"

    manager = ActorManager(actor_id=actor_with_account.actor_id, session=sql_session)

    assert [] == await manager.groups()


async def test_rename_actor_and_add_to_group(
    test_broker, actor_with_account, sql_session
):
    old_config = extension.configuration
    extension.configure({"automatically_add_users_to_group": True})

    await test_broker.publish(
        NameActorMessage(actor=actor_with_account.actor_id, name="sue"),
        routing_key="html_display_name",
        exchange=global_container.exchange,
    )

    actor = await sql_session.scalar(
        select(PublishingActor).where(
            PublishingActor.actor == actor_with_account.actor_id
        )
    )

    assert actor.name == "sue"

    manager = ActorManager(actor_id=actor_with_account.actor_id, session=sql_session)

    assert ["html_display"] == await manager.groups()

    extension.configuration = old_config
