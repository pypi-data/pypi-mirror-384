import pytest
from sqlalchemy import func

from cattle_grid.testing.fixtures import *  # noqa

from cattle_grid.database.account import Account, ActorForAccount
from .account import (
    account_with_name_password,
    create_account,
    delete_account,
    AccountAlreadyExists,
    InvalidAccountName,
    WrongPassword,
    add_permission,
    list_permissions,
    remove_permission,
    account_for_actor,
    add_actor_to_group,
    group_names_for_actor,
    actor_for_actor_id,
)


async def test_wrong_password(sql_session):
    sql_session.add(
        Account(
            name="name",
            password_hash="$argon2id$v=19$m=65536,t=3,p=4$MIIRqgvgQbgj220jfp0MPA$YfwJSVjtjSU0zzV/P3S9nnQ/USre2wvJMjfCIjrTQbg",
        )
    )
    await sql_session.commit()

    result = await account_with_name_password(sql_session, "name", "pass")

    assert result is None


async def test_create_and_then_get(sql_session):
    name = "user"
    password = "pass"

    await create_account(sql_session, name, password)

    result = await account_with_name_password(sql_session, name, password)

    assert result
    assert result.name == name


async def test_create_duplicate_raises_exception(sql_session):
    name = "user"
    password = "pass"

    await create_account(sql_session, name, password)

    with pytest.raises(AccountAlreadyExists):
        await create_account(sql_session, name, password)


@pytest.mark.parametrize(
    "name", ["", "abcdefghijklmnopqrstuvwxyz", "first.second", "admin"]
)
async def test_create_name_raises_exception(sql_session, name):
    with pytest.raises(InvalidAccountName):
        await create_account(sql_session, name, "pass")


async def test_create_and_then_delete_wrong_password(sql_session):
    name = "user"
    password = "pass"

    await create_account(sql_session, name, password)

    assert 1 == await sql_session.scalar(func.count(Account.id))

    with pytest.raises(WrongPassword):
        await delete_account(sql_session, name, "wrong")


async def test_create_and_then_delete(sql_session):
    name = "user"
    password = "pass"

    await create_account(sql_session, name, password)

    assert 1 == await sql_session.scalar(func.count(Account.id))

    await delete_account(sql_session, name, password)

    assert 0 == await sql_session.scalar(func.count(Account.id))


async def test_add_permission(sql_session):
    name = "user"
    password = "pass"

    account = await create_account(sql_session, name, password)
    assert account
    await add_permission(sql_session, account, "admin")
    await add_permission(sql_session, account, "test")

    await sql_session.refresh(account, attribute_names=["permissions"])

    assert set(list_permissions(account)) == {"admin", "test"}


async def test_remove_permission(sql_session):
    name = "user"
    password = "pass"

    account = await create_account(sql_session, name, password)
    assert account
    await add_permission(sql_session, account, "admin")
    await add_permission(sql_session, account, "test")

    await sql_session.refresh(account, attribute_names=["permissions"])

    assert set(list_permissions(account)) == {"admin", "test"}

    await remove_permission(sql_session, account, "admin")
    await sql_session.refresh(account, attribute_names=["permissions"])
    assert set(list_permissions(account)) == {"test"}


async def test_account_for_actor_not_found(sql_session):
    account_or_none = await account_for_actor(sql_session, "http://actor.example")

    assert account_or_none is None


async def test_account_for_actor(sql_session):
    account = await create_account(sql_session, "name", "password")
    actor_id = "http://actor.example"

    sql_session.add(ActorForAccount(account=account, actor=actor_id))
    await sql_session.commit()

    result = await account_for_actor(sql_session, actor_id)

    assert result == account

    result_actor = await actor_for_actor_id(sql_session, actor_id)
    assert result_actor
    assert result_actor.actor == actor_id


async def test_account_groups(sql_session):
    account = await create_account(sql_session, "name", "password")
    actor_id = "http://actor.example"

    actor_for_account = ActorForAccount(account=account, actor=actor_id)
    sql_session.add(actor_for_account)
    await sql_session.commit()

    await add_actor_to_group(sql_session, actor_for_account, "group1")
    await add_actor_to_group(sql_session, actor_for_account, "group2")

    result = await group_names_for_actor(sql_session, actor_for_account)

    assert set(result) == {"group1", "group2"}
