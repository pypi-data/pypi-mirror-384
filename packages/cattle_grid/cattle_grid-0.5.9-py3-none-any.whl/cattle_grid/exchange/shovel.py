import logging
from typing import Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from bovine.activitystreams.utils import id_for_object

from cattle_grid.dependencies.internals import Transformer
from cattle_grid.model import ActivityMessage
from cattle_grid.database.activity_pub_actor import Actor, Blocking

from cattle_grid.dependencies import (
    AccountExchangePublisher,
    ActivityExchangePublisher,
    SqlSession,
)


from cattle_grid.database.account import ActorForAccount
from cattle_grid.model.account import EventInformation, EventType

logger = logging.getLogger(__name__)


async def should_shovel_activity(session: AsyncSession, activity: dict) -> bool:
    """Some activities like Block or Undo Block should not be visible to the user. This method
    returns False if this is the case."""

    activity_type = activity.get("type")

    if activity_type == "Block":
        return False

    if activity_type == "Undo":
        object_id = id_for_object(activity.get("object"))
        blocking = await session.scalar(
            func.count(
                select(Blocking.id)
                .where(Blocking.request == object_id)
                .scalar_subquery()
            )
        )

        if blocking:
            return False

    return True


async def shovel(
    actor: str,
    activity: dict[str, Any],
    session: SqlSession,
    transformer: Transformer,
    publisher: ActivityExchangePublisher,
    account_publisher: AccountExchangePublisher,
    direction: EventType,
):
    actor_for_account = await session.scalar(
        select(ActorForAccount).where(ActorForAccount.actor == actor)
    )
    if actor_for_account is None:
        logger.warning("Got actor without account %s", actor)
        return

    account_name = actor_for_account.account.name
    to_shovel = await transformer({"raw": activity}, actor_id=actor)
    activity_type = activity.get("type")

    event_info = EventInformation(
        actor=actor,
        event_type=direction,
        data=to_shovel,
    )

    await account_publisher(
        event_info,
        routing_key=f"receive.{account_name}.{str(direction)}",
    )
    await account_publisher(
        event_info,
        routing_key=f"receive.{account_name}.{str(direction)}.{activity_type}",
    )
    await publisher(
        ActivityMessage(actor=actor, data=to_shovel),
        routing_key=f"{str(direction)}.{activity_type}",
    )


async def incoming_shovel(
    msg: ActivityMessage,
    session: SqlSession,
    transformer: Transformer,
    publisher: ActivityExchangePublisher,
    account_publisher: AccountExchangePublisher,
) -> None:
    """Transfers the message from the RawExchange to the
    Activity- and Account one.

    The message is passed through the transformer.
    """
    logger.info("incoming shovel")

    if not await should_shovel_activity(session, msg.data):
        return

    # FIXME: Use join to combine the next two queries ...

    db_actor = await session.scalar(select(Actor).where(Actor.actor_id == msg.actor))
    if not db_actor:
        raise ValueError("Actor not found in database")

    blocking = await session.scalar(
        select(Blocking)
        .where(Blocking.actor == db_actor)
        .where(Blocking.blocking == msg.data.get("actor"))
        .where(Blocking.active)
    )
    if blocking:
        return

    return await shovel(
        msg.actor,
        msg.data,
        direction=EventType.incoming,
        transformer=transformer,
        publisher=publisher,
        account_publisher=account_publisher,
        session=session,
    )


async def outgoing_shovel(
    msg: ActivityMessage,
    transformer: Transformer,
    publisher: ActivityExchangePublisher,
    account_publisher: AccountExchangePublisher,
    session: SqlSession,
) -> None:
    return await shovel(
        msg.actor,
        msg.data,
        direction=EventType.outgoing,
        transformer=transformer,
        publisher=publisher,
        account_publisher=account_publisher,
        session=session,
    )
