from cattle_grid.database.activity_pub_actor import Blocking
from .testing import *  # noqa


def test_get_object_not_found(test_client):
    response = test_client.get(
        "/html_display/object/2fd16a00-309b-4f3a-9d91-aa9516e59c1f"
    )
    assert response.status_code == 404


def test_get_object(test_client, published_object):
    assert published_object

    object_id = published_object["id"]

    response = test_client.get(
        object_id,
        headers={
            "x-ap-location": object_id,
            "x-cattle-grid-requester": "http://remote.test/actor",
        },
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/activity+json"
    data = response.json()

    assert data["replies"] == object_id + "/replies"


def test_get_object_wrong_location(test_client, published_object):
    assert published_object

    object_id = published_object["id"]

    response = test_client.get(
        object_id,
        headers={
            "x-ap-location": "http://wrong.test",
            "x-cattle-grid-requester": "http://remote.test/actor",
        },
    )

    assert response.status_code == 404


def test_get_object_unauthorized(test_client, published_object):
    assert published_object

    object_id = published_object["id"]

    response = test_client.get(
        object_id,
        headers={
            "x-ap-location": object_id,
        },
    )

    assert response.status_code == 401


async def test_get_object_blocked(
    test_client, published_object, actor_for_test, sql_session
):
    remote_actor = "http://remote.test/actor"

    object_id = published_object["id"]
    sql_session.add(
        Blocking(
            actor=actor_for_test,
            blocking=remote_actor,
            active=True,
            request=actor_for_test.actor_id + "#block",
        )
    )
    await sql_session.commit()

    response = test_client.get(
        object_id,
        headers={
            "x-ap-location": object_id,
            "x-cattle-grid-requester": remote_actor,
        },
    )

    assert response.status_code == 401
