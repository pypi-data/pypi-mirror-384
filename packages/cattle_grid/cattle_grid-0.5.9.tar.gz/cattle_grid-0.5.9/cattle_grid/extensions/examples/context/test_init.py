import pytest
from sqlalchemy import select
from cattle_grid.extensions.load import build_transformer
from cattle_grid.testing.fixtures import *  # noqa
from cattle_grid.extensions.util import lifespan_for_sql_alchemy_base_class

from muck_out.extension import extension as muck_out


from . import extension
from .models import Base, ContextInformation


@pytest.fixture(autouse=True)
async def create_tables(sql_engine_for_tests):
    lifespan = lifespan_for_sql_alchemy_base_class(Base)
    async with lifespan(sql_engine_for_tests):
        yield


@pytest.fixture
def transformer():
    return build_transformer([muck_out, extension])


async def test_transform_accept(transformer, actor_for_test):
    result = await transformer(
        {
            "raw": {
                "@context": "https://www.w3.org/ns/activitystreams",
                "id": "http://remote.test/obj_id",
                "type": "Accept",
                "actor": "http://remote.test/actor",
                "object": "http://local.test/follow_id",
                "to": "http://local.test/actor",
            }
        },
        actor_id=actor_for_test.actor_id,
    )

    assert result.get("context") == {}


def activity_for_test(object_id: str, in_reply_to: str | None = None):
    obj = {
        "attributedTo": "http://actor.example",
        "content": "<i>italic</i>",
        "id": object_id,
        "published": "2025-09-09T09:32:39Z",
        "to": [
            "https://www.w3.org/ns/activitystreams#Public",
            "http://remote.example/",
        ],
        "type": "Note",
    }

    if in_reply_to:
        obj["inReplyTo"] = in_reply_to

    return {
        "@context": [
            "https://www.w3.org/ns/activitystreams",
            {"Hashtag": "as:Hashtag", "sensitive": "as:sensitive"},
        ],
        "actor": "http://actor.example",
        "id": object_id + "/activity",
        "object": obj,
        "published": "2025-09-09T09:32:39Z",
        "to": [
            "https://www.w3.org/ns/activitystreams#Public",
            "http://remote.example/",
        ],
        "type": "Create",
    }


async def test_transform_create_object(transformer, sql_session, actor_for_test):
    object_id = "http://actor.example/object/x36yl8P2Rx8"
    activity = activity_for_test(object_id)

    result = await transformer({"raw": activity}, actor_id=actor_for_test.actor_id)

    context_info = await sql_session.scalar(
        select(ContextInformation).where(ContextInformation.object_id == object_id)
    )

    assert context_info

    assert result["context"]["id"] == str(context_info.context_id)


async def test_transform_create_object_idempotent(transformer, actor_for_test):
    object_id = "http://actor.example/object/x36yl8P2Rx8"
    activity = activity_for_test(object_id)

    one = await transformer({"raw": activity}, actor_id=actor_for_test.actor_id)
    two = await transformer({"raw": activity}, actor_id=actor_for_test.actor_id)

    assert one == two


async def test_transform_object_and_reply_same_context(transformer, actor_for_test):
    object_id = "http://actor.example/object/x36yl8P2Rx8"
    reply_id = "http://remote.example/object/d7s6d78dsaf"
    activity = activity_for_test(object_id)
    reply = activity_for_test(reply_id, in_reply_to=object_id)

    one = await transformer({"raw": activity}, actor_id=actor_for_test.actor_id)
    two = await transformer({"raw": reply}, actor_id=actor_for_test.actor_id)

    assert one.get("context") == two.get("context")
