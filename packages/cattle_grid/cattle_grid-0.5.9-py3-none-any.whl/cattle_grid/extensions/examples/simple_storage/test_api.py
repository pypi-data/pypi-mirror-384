import pytest

from uuid import uuid4
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.future import select

from fastapi import FastAPI
from fastapi.testclient import TestClient
from cattle_grid.dependencies.globals import global_container

from cattle_grid.testing.fixtures import *  # noqa

from . import extension
from .message_types import PublishObject
from .test_handlers import object_stub, sql_engine, test_broker, send_message_mock  # noqa
from .models import StoredActivity, StoredObject


@pytest.fixture
async def stored_uuids(sql_engine, actor_for_test, test_broker):  # noqa
    obj = object_stub.copy()
    obj["attributedTo"] = actor_for_test.actor_id
    msg = PublishObject(actor=actor_for_test.actor_id, data=obj)

    async_session = async_sessionmaker(sql_engine, expire_on_commit=False)

    await test_broker.publish(
        msg, routing_key="publish_object", exchange=global_container.exchange
    )

    async with async_session() as session:
        result = (await session.scalars(select(StoredActivity))).all()

        activity_uuid = result[0].data.get("id")

        result = (await session.scalars(select(StoredObject))).all()

        object_uuid = result[0].data.get("id")

    return activity_uuid, object_uuid


@pytest.fixture
def object_ids(stored_uuids):
    _, object_uuid = stored_uuids
    return object_uuid, object_uuid.split("/")[-1]


@pytest.fixture
def activity_ids(stored_uuids):
    activity_uuid, _ = stored_uuids
    return activity_uuid, activity_uuid.split("/")[-1]


@pytest.fixture
def test_client():
    app = FastAPI()
    app.include_router(extension.api_router)

    return TestClient(app)


def test_not_found(test_client):
    response = test_client.get(
        f"/{uuid4()}",
        headers={
            "x-cattle-grid-requester": "http://bob.example",
            "x-ap-location": "location",
        },
    )

    assert response.status_code == 404


def test_get_activity(activity_ids, test_client):
    activity_id, activity_uuid = activity_ids

    response = test_client.get(
        f"/{activity_uuid}",
        headers={
            "x-cattle-grid-requester": "http://bob.example",
            "x-ap-location": activity_id,
        },
    )

    assert response.status_code == 200
    assert response.json()["type"] == "Create"
    assert response.headers["content-type"] == "application/activity+json"


def test_get_activity_unauthorized(activity_ids, test_client):
    activity_id, activity_uuid = activity_ids

    response = test_client.get(
        f"/{activity_uuid}",
        headers={
            "x-ap-location": activity_id,
        },
    )

    assert response.status_code == 401


def test_get_object(object_ids, test_client):
    object_id, object_uuid = object_ids

    response = test_client.get(
        f"/{object_uuid}",
        headers={
            "x-cattle-grid-requester": "http://bob.example",
            "x-ap-location": object_id,
        },
    )

    assert response.status_code == 200
    assert response.json()["type"] == "Note"
    assert response.headers["content-type"] == "application/activity+json"


def test_get_object_unauthorized(object_ids, test_client):
    object_id, object_uuid = object_ids

    response = test_client.get(
        f"/{object_uuid}",
        headers={
            "x-cattle-grid-requester": "http://unknown.example",
            "x-ap-location": object_id,
        },
    )

    assert response.status_code == 401


def test_get_object_wrong_location(object_ids, test_client):
    object_id, object_uuid = object_ids

    response = test_client.get(
        f"/{object_uuid}",
        headers={
            "x-cattle-grid-requester": "http://bob.example",
            "x-ap-location": "nowhere",
        },
    )

    assert response.status_code == 400
