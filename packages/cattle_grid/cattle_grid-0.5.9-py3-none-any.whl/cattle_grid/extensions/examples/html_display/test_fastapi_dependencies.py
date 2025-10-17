from fastapi import HTTPException
import pytest


from .testing import *  # noqa
from .fastapi_dependencies import publishing_actor_for_name


async def test_publishing_actor_for_name(sql_session):
    with pytest.raises(HTTPException):
        await publishing_actor_for_name(sql_session, "name")
