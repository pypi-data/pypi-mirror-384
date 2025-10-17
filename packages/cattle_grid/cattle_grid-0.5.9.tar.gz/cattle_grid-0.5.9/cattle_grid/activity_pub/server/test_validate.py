from fastapi import HTTPException
import pytest

from cattle_grid.testing.fixtures import *  # noqa

from .validate import validate_actor, validate_request


def test_validate_actor_none():
    with pytest.raises(HTTPException):
        validate_actor(None)


async def test_validate_request(actor_for_test, sql_session):
    with pytest.raises(HTTPException):
        await validate_request(sql_session, actor_for_test, None)
