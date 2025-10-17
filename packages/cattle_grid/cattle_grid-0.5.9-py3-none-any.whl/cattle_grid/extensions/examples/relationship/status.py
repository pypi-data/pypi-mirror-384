from .types import Relationship, RelationshipStatus


def determine_status(info: list[tuple[bool, str]]) -> Relationship:
    if len(info) == 0:
        return Relationship(status=RelationshipStatus.none)

    status = (
        RelationshipStatus.accepted
        if any(x[0] for x in info)
        else RelationshipStatus.waiting
    )
    requests = [x[1] for x in info]

    return Relationship(status=status, requests=requests)
