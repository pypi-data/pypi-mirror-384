from sqlalchemy import select
from cattle_grid.testing.fixtures import *  # noqa
from cattle_grid.database.account import ActorForAccount
from cattle_grid.model.exchange_update_actor import RenameActorAction

from .actor_update import handle_actor_action


async def test_handle_actor_action_rename(actor_with_account, sql_session):
    action = RenameActorAction(name="new name")

    await handle_actor_action(actor_with_account, sql_session, action)

    actor_for_account = await sql_session.scalar(
        select(ActorForAccount).where(
            ActorForAccount.actor == actor_with_account.actor_id
        )
    )
    assert actor_for_account.name == "new name"
