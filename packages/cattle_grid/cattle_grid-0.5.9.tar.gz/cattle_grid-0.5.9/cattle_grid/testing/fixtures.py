import pytest

from sqlalchemy.ext.asyncio import async_sessionmaker

from cattle_grid.account.account import create_account, add_actor_to_account
from cattle_grid.activity_pub.actor import create_actor

from cattle_grid.config.auth import new_auth_config, save_auth_config
from cattle_grid.database.account import Account
from cattle_grid.database.activity_pub_actor import Actor
from cattle_grid.dependencies.globals import global_container

from cattle_grid.database.activity_pub import Base as APBase

__all__ = [
    "sql_engine_for_tests",
    "session_maker_for_tests",
    "sql_session",
    "actor_for_test",
    "account_for_test",
    "actor_with_account",
    "auth_config",
    "auth_config_file",
    "loaded_config",
]


@pytest.fixture(autouse=True)
async def sql_engine_for_tests():
    """Provides the sql engine (as in memory sqlite) for tests

    This fixture has autouse=True, meaning that by importing

    ```python
    from cattle_grid.testing.fixtures import sql_engine_for_tests
    ```

    it will run automatically. The engine is initialized in the
    place cattle_grid expects it.
    """
    async with global_container.alchemy_database(
        "sqlite+aiosqlite:///:memory:", echo=False
    ) as engine:
        async with engine.begin() as conn:
            await conn.run_sync(APBase.metadata.create_all)

        yield engine


@pytest.fixture()
async def session_maker_for_tests(sql_engine_for_tests):
    yield async_sessionmaker(sql_engine_for_tests, expire_on_commit=False)


@pytest.fixture()
async def sql_session(session_maker_for_tests):
    """Returns an [AsyncSession][sqlalchemy.ext.asyncio.AsyncSession] to be used by tests"""
    async with session_maker_for_tests() as session:
        yield session


@pytest.fixture
async def account_for_test(sql_session) -> Account:
    """Fixture to create an account"""
    result = await create_account(sql_session, "alice", "alice", permissions=["admin"])
    assert result
    return result


@pytest.fixture
async def actor_for_test(sql_session) -> Actor:
    """Fixture to create an actor"""
    actor = await create_actor(sql_session, "http://localhost/ap")

    return actor


@pytest.fixture
async def actor_with_account(sql_session, account_for_test) -> Actor:
    """Fixture to create an actor with an account"""
    actor = await create_actor(sql_session, "http://localhost/ap")
    await add_actor_to_account(
        sql_session, account_for_test, actor, name="test_fixture"
    )

    await sql_session.refresh(actor)

    return actor


@pytest.fixture
def auth_config():
    config = new_auth_config(actor_id="http://localhost/actor_id", username="actor")

    config.domain_blocks = set(["blocked.example"])

    return config


@pytest.fixture
def auth_config_file(tmp_path, auth_config):
    filename = tmp_path / "auth_config.toml"

    save_auth_config(filename, auth_config)

    return filename


@pytest.fixture(autouse=True, scope="session")
def loaded_config():
    """Ensures the configuration variables are loaded"""
    global_container.load_config()
