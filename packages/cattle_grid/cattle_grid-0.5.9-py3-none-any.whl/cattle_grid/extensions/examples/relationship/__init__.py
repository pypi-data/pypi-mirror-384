import logging
from typing import Any

from sqlalchemy import select
from cattle_grid.database.activity_pub_actor import Blocking, Follower, Following
from cattle_grid.dependencies import SqlSession
from cattle_grid.dependencies.transformer import ActorTransforming
from cattle_grid.extensions import Extension

from muck_out.cattle_grid import TransformedActor

from cattle_grid.extensions.examples.relationship.status import determine_status

extension = Extension("relationship", __name__)

logger = logging.getLogger(__name__)


@extension.transform(inputs=["parsed"], outputs=["releationship"])
async def transform(
    transformed_actor: TransformedActor, actor: ActorTransforming, session: SqlSession
) -> dict[str, Any]:
    if transformed_actor is None:
        return {"relationship": {}}

    logger.info("Processing relationships")

    result = {}

    follower = await session.execute(
        select(Follower.accepted, Follower.request)
        .where(Follower.actor == actor)
        .where(Follower.follower == transformed_actor.id)
    )
    following = await session.execute(
        select(Following.accepted, Following.request)
        .where(Following.actor == actor)
        .where(Following.following == transformed_actor.id)
    )
    blocking = await session.execute(
        select(Blocking.active, Blocking.request)
        .where(Blocking.actor == actor)
        .where(Blocking.blocking == transformed_actor.id)
    )

    result["follower"] = determine_status(follower.all()).model_dump()  # type: ignore
    result["following"] = determine_status(following.all()).model_dump()  # type: ignore
    result["blocking"] = determine_status(blocking.all()).model_dump()  # type: ignore

    return {"relationship": result}
