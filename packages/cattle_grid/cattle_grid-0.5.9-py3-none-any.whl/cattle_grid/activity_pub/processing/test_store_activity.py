from unittest.mock import AsyncMock

from sqlalchemy import func
from cattle_grid.testing.fixtures import *  # noqa

from cattle_grid.database.activity_pub_actor import StoredActivity
from cattle_grid.model.processing import StoreActivityMessage

from .store_activity import store_activity_subscriber


async def test_store_activity(sql_session, actor_for_test):
    publisher = AsyncMock()
    activity = {
        "actor": actor_for_test.actor_id,
        "type": "Activity",
        "to": ["http://remote.test/actor"],
    }
    msg = StoreActivityMessage(actor=actor_for_test.actor_id, data=activity)

    await store_activity_subscriber(
        msg, actor_for_test, session=sql_session, publisher=publisher
    )
    await sql_session.commit()

    assert 1 == await sql_session.scalar(func.count(StoredActivity.id))

    publisher.assert_awaited_once()
