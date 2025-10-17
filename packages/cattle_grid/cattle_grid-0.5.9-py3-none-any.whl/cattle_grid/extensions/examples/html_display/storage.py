import logging
import random
import string
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from cattle_grid.extensions.examples.html_display.database import (
    PublishedObject,
    PublishingActor,
)


logger = logging.getLogger(__name__)


def new_name():
    return "".join(random.choices(string.ascii_letters, k=12))


async def publishing_actor_for_actor_id(session: AsyncSession, actor_id: str):
    actor = await session.scalar(
        select(PublishingActor).where(PublishingActor.actor == actor_id)
    )
    if actor:
        return actor

    actor = PublishingActor(actor=actor_id, name=new_name())
    session.add(actor)
    await session.commit()
    await session.refresh(actor)
    return actor


async def object_for_object_id(
    session: AsyncSession, object_id: str
) -> PublishedObject | None:
    try:
        object_uuid = UUID(object_id.split("/")[-1])
    except Exception:
        return None

    return await session.scalar(
        select(PublishedObject).where(PublishedObject.id == object_uuid)
    )
