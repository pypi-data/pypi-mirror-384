import pytest

from cattle_grid.testing.fixtures import *  # noqa

from . import list_actors, show_actor


@pytest.mark.parametrize("deleted", [True, False])
async def test_list_actors(sql_session, deleted):
    await list_actors(sql_session, deleted)


async def test_show_actor(sql_session, actor_with_account):
    await show_actor(sql_session, actor_with_account.actor_id)
