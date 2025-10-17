from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from cattle_grid.database.activity_pub_actor import Actor, ActorStatus
from cattle_grid.activity_pub.actor.relationship import is_blocked


def validate_actor(actor: Actor | None) -> Actor:
    if actor is None:
        raise HTTPException(404)
    if actor.status == ActorStatus.deleted:
        raise HTTPException(410)

    return actor


async def validate_request(
    session: AsyncSession, actor: Actor | None, requester: str | None
) -> Actor:
    if requester is None:
        raise HTTPException(401)

    actor = validate_actor(actor)

    if await is_blocked(session, actor, requester):
        raise HTTPException(403)

    return actor
