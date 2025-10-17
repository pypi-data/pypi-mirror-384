from uuid import uuid4
import pytest

from cattle_grid.extensions.examples.html_display.database import ExportPermission

from .storage import publishing_actor_for_actor_id

from .testing import *  # noqa


def test_get_object_html(test_client, published_object):
    assert published_object
    url_in_obj = published_object.get("url", [])
    url = url_in_obj[0].get("href").replace("@", "html_display/html/")

    response = test_client.get(url)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")


async def test_get_object_html_not_found(test_client, publishing_actor_for_test):
    response = test_client.get(
        f"/html_display/html/{publishing_actor_for_test.name}/2fd16a00-309b-4f3a-9d91-aa9516e59c1f"
    )

    assert response.status_code == 404


async def test_get_object_html_actor_mismatch(
    sql_session, test_client, published_object
):
    actor = await publishing_actor_for_actor_id(sql_session, "some_id")
    await sql_session.commit()

    response = test_client.get(
        f"/html_display/html/{actor.name}/" + published_object.get("id").split("/")[-1]
    )

    assert response.status_code == 404


@pytest.mark.parametrize(
    "query,status",
    [
        ("", 422),
        ("?token=test", 422),
        ("?token=f47ac10b-58cc-4372-a567-0e02b2c3d479", 401),
    ],
)
async def test_export_objects_unauthorized(
    publishing_actor_for_test, test_client, query, status
):
    response = test_client.get(
        f"/html_display/html/{publishing_actor_for_test.name}/export{query}"
    )

    assert response.status_code == status


async def test_export_objects_authorized(
    sql_session, test_client, publishing_actor_for_test
):
    uuid = uuid4()
    sql_session.add(
        ExportPermission(
            publishing_actor=publishing_actor_for_test, one_time_token=uuid
        )
    )

    await sql_session.commit()

    response = test_client.get(
        f"/html_display/html/{publishing_actor_for_test.name}/export?token={uuid}"
    )

    assert response.status_code == 200
    data = response.json()

    assert data["type"] == "OrderedCollection"


async def test_export_objects_with_object(
    sql_session, test_client, publishing_actor_for_test, published_object
):
    uuid = uuid4()
    sql_session.add(
        ExportPermission(
            publishing_actor=publishing_actor_for_test, one_time_token=uuid
        )
    )

    await sql_session.commit()

    response = test_client.get(
        f"/html_display/html/{publishing_actor_for_test.name}/export?token={uuid}"
    )

    assert response.status_code == 200
    data = response.json()

    assert data["type"] == "OrderedCollection"

    assert data["totalItems"] == 1
    assert len(data["orderedItems"]) == 1
