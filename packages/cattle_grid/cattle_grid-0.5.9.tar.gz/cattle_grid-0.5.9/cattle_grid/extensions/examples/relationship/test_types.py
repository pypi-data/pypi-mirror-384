from .types import Relationship, RelationshipStatus


def test_serialization():
    r = Relationship(status=RelationshipStatus.accepted)

    assert r.model_dump_json() == """{"status":"accepted","requests":[]}"""
