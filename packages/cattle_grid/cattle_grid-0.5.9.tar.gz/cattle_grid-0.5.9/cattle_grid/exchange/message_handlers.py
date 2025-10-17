import logging

from cattle_grid.activity_pub.enqueuer import determine_activity_type
from cattle_grid.activity_pub.processing.common import MessageBovineActor
from cattle_grid.dependencies import (
    InternalExchangePublisher,
    InternalExchangeRequester,
)
from cattle_grid.dependencies.internals import LookupAnnotation, Transformer
from cattle_grid.model import ActivityMessage, FetchMessage


logger = logging.getLogger(__name__)


async def send_message(
    msg: ActivityMessage,
    publisher: InternalExchangePublisher,
) -> None:
    """Takes a message and ensure it is distributed appropriately"""

    content = msg.data
    activity_type = determine_activity_type(content)

    if not activity_type:
        return

    to_send = ActivityMessage(actor=msg.actor, data=content)

    await publisher(
        to_send,
        routing_key=f"outgoing.{activity_type}",
    )


async def fetch_object(msg: FetchMessage, requester: InternalExchangeRequester) -> dict:
    """Used to fetch an object as an RPC method"""
    result = await requester(
        msg,
        routing_key="fetch_object",
    )
    return result


async def fetch(
    message: FetchMessage,
    transformer: Transformer,
    lookup: LookupAnnotation,
    actor: MessageBovineActor,
) -> dict:
    """Used to fetch an object as an RPC method. In difference to `fetch_object`,
    this method applies the transformer."""

    from cattle_grid.activity_pub.processing.remote import fetch_object

    logger.info("fetch started")
    result = await fetch_object(
        message,
        actor,
        lookup,
    )
    logger.info("fetch done", result)

    transformed = await transformer({"raw": result}, actor_id=message.actor)
    return transformed
