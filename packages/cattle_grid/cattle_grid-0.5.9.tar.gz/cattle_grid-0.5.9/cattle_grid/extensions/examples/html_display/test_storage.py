from .database import PublishingActor
from .storage import object_for_object_id, publishing_actor_for_actor_id

from .testing import *  # noqa


async def test_publishing_actor_for_actor_id(sql_session):
    actor_id = "http://actor.test/some/id"

    result = await publishing_actor_for_actor_id(sql_session, actor_id)

    assert isinstance(result, PublishingActor)
    assert result.actor == actor_id


async def test_publishing_actor_for_actor_id_returns_stored_actor(sql_session):
    actor_id = "http://actor.test/some/id"

    one = await publishing_actor_for_actor_id(sql_session, actor_id)

    await sql_session.commit()

    two = await publishing_actor_for_actor_id(sql_session, actor_id)

    assert one.name == two.name


async def test_object_for_object_id_unknown(sql_session):
    object_id = "http://object.test/some/id"

    result = await object_for_object_id(sql_session, object_id)

    assert result is None


async def test_object_for_object_id(sql_session, published_object):
    object_id = published_object.get("id")

    result = await object_for_object_id(sql_session, object_id)

    assert result
