"""
These are annotations useable when building a transformer in an extension,
see [here](../extensions/index.md#transformers).

Furthermore, you may use the annotations from [muck_out.cattle_grid][] starting
with Fetch or Transformed.
"""

from typing import Annotated
from fast_depends import Depends
from sqlalchemy import select
from cattle_grid.database.activity_pub_actor import Actor
from cattle_grid.dependencies import SqlSession


async def actor_for_transformer(session: SqlSession, actor_id: str) -> Actor:
    actor = await session.scalar(select(Actor).where(Actor.actor_id == actor_id))

    if actor is None:
        raise Exception("Actor not found")

    return actor


ActorTransforming = Annotated[Actor, Depends(actor_for_transformer)]
"""The actor in whose scope the transformation is running"""
