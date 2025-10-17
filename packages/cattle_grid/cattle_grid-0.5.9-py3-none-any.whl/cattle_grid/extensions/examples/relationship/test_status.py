from cattle_grid.extensions.examples.relationship.types import RelationshipStatus
from .status import determine_status


def test_determine_status_empty():
    result = determine_status([])

    assert result.status == RelationshipStatus.none


def test_determine_status_accepted():
    result = determine_status(
        [(False, "http://request.test/one"), (True, "http://request.test/two")]
    )

    assert result.status == RelationshipStatus.accepted
    assert result.requests == ["http://request.test/one", "http://request.test/two"]


def test_determine_status_waiting():
    result = determine_status(
        [(False, "http://request.test/one"), (False, "http://request.test/two")]
    )

    assert result.status == RelationshipStatus.waiting
    assert result.requests == ["http://request.test/one", "http://request.test/two"]
