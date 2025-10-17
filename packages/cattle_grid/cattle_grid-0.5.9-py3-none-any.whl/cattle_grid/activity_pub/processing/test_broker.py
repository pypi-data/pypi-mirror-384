from cattle_grid.dependencies.globals import global_container

from .testing import *  # noqa


async def test_shared_inbox(actor_for_test, broker, mock_incoming_activity):
    activity = {
        "actor": "http://remote.test/actor",
        "type": "Activity",
        "to": [actor_for_test.actor_id],
    }

    await broker.publish(
        {"data": activity},
        routing_key="shared_inbox",
        exchange=global_container.internal_exchange,
    )

    mock_incoming_activity.assert_awaited_once()
