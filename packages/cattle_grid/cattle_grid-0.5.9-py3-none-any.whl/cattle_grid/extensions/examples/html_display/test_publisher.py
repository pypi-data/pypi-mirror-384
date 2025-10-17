from unittest.mock import MagicMock

import pytest

from .config import HtmlDisplayConfiguration
from .publisher import Publisher


@pytest.fixture
def publisher():
    return Publisher(
        actor=MagicMock(actor="http://actor.test/", name="name"),
        config=HtmlDisplayConfiguration(),
        obj={},
    )


def test_id_stays_idempotent(publisher):
    stored_object = publisher.object_for_store

    new_publisher = Publisher(
        actor=MagicMock(actor="http://actor.test/", name="name"),
        config=HtmlDisplayConfiguration(),
        obj=stored_object,
    )

    new_id = new_publisher.object_for_store.get("id")

    assert new_id == stored_object.get("id")
    assert publisher.uuid == new_publisher.uuid


def test_create_html_link(publisher):
    result = publisher.create_html_link()

    assert isinstance(result, dict)


def test_object_for_remote(publisher) -> None:
    obj = publisher.object_for_remote

    assert isinstance(obj.get("url"), list)

    object_id = obj.get("id")
    assert isinstance(object_id, str)
    assert obj.get("replies") == object_id + "/replies"
    assert obj.get("shares") == object_id + "/shares"
    assert obj.get("likes") == object_id + "/likes"
