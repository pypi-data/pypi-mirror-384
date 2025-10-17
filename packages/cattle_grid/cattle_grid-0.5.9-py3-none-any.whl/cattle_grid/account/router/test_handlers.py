import pytest
from unittest.mock import AsyncMock
from sqlalchemy import select
from cattle_grid.account.account import add_permission
from cattle_grid.database.account import Account, ActorForAccount

from cattle_grid.testing.fixtures import *  # noqa

from cattle_grid.model.account import CreateActorRequest
from .router import create_actor_handler


async def test_create_actor_handler_no_permission(sql_session):
    account = Account(name="test", password_hash="")
    sql_session.add(account)
    await sql_session.commit()

    with pytest.raises(ValueError):
        await create_actor_handler(
            CreateActorRequest(base_url="http://abel", preferred_username="username"),
            account=account,
            session=sql_session,
            responder=AsyncMock(),
        )


async def test_create_actor_handler(sql_session):
    account = Account(name="test", password_hash="")
    sql_session.add(account)
    await sql_session.commit()
    await add_permission(sql_session, account, "admin")
    responder = AsyncMock()

    await create_actor_handler(
        CreateActorRequest(base_url="http://abel", preferred_username="username"),
        account=account,
        responder=responder,
        session=sql_session,
    )

    result = [x for x in await sql_session.scalars(select(ActorForAccount))]

    assert len(result) == 1

    responder.respond.assert_awaited_once()

    (
        _,
        data,
    ) = responder.respond.call_args[0]

    assert data["id"] == result[0].actor
    assert data["preferredUsername"] == "username"
