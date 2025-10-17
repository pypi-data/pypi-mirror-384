from unittest.mock import AsyncMock

from sqlalchemy import select

from cattle_grid.testing.fixtures import *  # noqa
from cattle_grid.model.account import TriggerMessage

from cattle_grid.account.account import add_actor_to_group
from cattle_grid.database.account import ActorForAccount
from cattle_grid.config.rewrite import RewriteConfiguration

from .trigger import handle_trigger


async def test_handle_trigger(sql_session, actor_with_account):
    publisher = AsyncMock()
    actor_for_account = await sql_session.scalar(
        select(ActorForAccount).where(
            ActorForAccount.actor == actor_with_account.actor_id
        )
    )
    assert actor_for_account

    await handle_trigger(
        TriggerMessage(
            actor=actor_with_account.actor_id,  # type:ignore
        ),
        session=sql_session,
        actor=actor_for_account,
        publisher=publisher,
        method="method",
        rewrite_rules=RewriteConfiguration.from_rules({}),
    )

    publisher.assert_awaited_once()

    (_, kwargs) = publisher.call_args

    assert kwargs["routing_key"] == "method"


async def test_handle_trigger_with_rewrite(sql_session, actor_with_account):
    publisher = AsyncMock()
    actor_for_account = await sql_session.scalar(
        select(ActorForAccount).where(
            ActorForAccount.actor == actor_with_account.actor_id
        )
    )
    assert actor_for_account

    await add_actor_to_group(sql_session, actor_for_account, "group")

    rewrite_config = {
        "group": {
            "method": "changed",
        }
    }

    await handle_trigger(
        TriggerMessage(
            actor=actor_with_account.actor_id,
        ),
        session=sql_session,
        actor=actor_for_account,
        publisher=publisher,
        method="method",
        rewrite_rules=RewriteConfiguration.from_rules(rewrite_config),
    )

    publisher.assert_awaited_once()

    (_, kwargs) = publisher.call_args

    assert kwargs["routing_key"] == "changed"
