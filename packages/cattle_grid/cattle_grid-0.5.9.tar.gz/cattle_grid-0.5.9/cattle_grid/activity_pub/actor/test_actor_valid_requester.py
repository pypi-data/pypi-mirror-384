import pytest

from cattle_grid.testing.fixtures import *  # noqa
from cattle_grid.database.activity_pub_actor import Follower, Blocking


from . import create_actor
from .requester import is_valid_requester


@pytest.fixture
async def test_actor(sql_session):
    actor = await create_actor(sql_session, "http://localhost/ap/")

    sql_session.add_all(
        [
            Follower(
                actor=actor,
                follower="http://follower.test",
                accepted=True,
                request="xxx",
            ),
            Blocking(
                actor=actor, blocking="http://blocking.test", active=True, request="xxx"
            ),
        ]
    )
    await sql_session.commit()

    return actor


@pytest.mark.parametrize(
    "obj,expected",
    [
        ({}, False),
        ({"to": ["http://remote.example"]}, True),
        ({"to": ["as:Public"]}, True),
    ],
)
async def test_is_valid_requester_remote(sql_session, test_actor, obj, expected):
    valid = await is_valid_requester(
        sql_session, "http://remote.example", test_actor, obj
    )

    assert valid == expected


@pytest.mark.parametrize(
    "obj,expected",
    [
        ({}, False),
        ({"to": ["http://blocking.test"]}, False),
        ({"to": ["as:Public"]}, False),
    ],
)
async def test_is_valid_requester_blocking(sql_session, test_actor, obj, expected):
    valid = await is_valid_requester(
        sql_session, "http://blocking.test", test_actor, obj
    )

    assert valid == expected
