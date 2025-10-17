"""

<div class="grid cards" markdown>

- [:material-api:{ .lg .middle } __OpenAPI__](../assets/redoc.html?url=openapi_simple_html_display.json)
- [:material-file-code:{ .lg .middle } __Source__](https://codeberg.org/bovine/cattle_grid/src/branch/main/cattle_grid/extensions/examples/html_display)

</div>


The goal of this extension is to illustrate the mechanism how cattle_grid
can be used to create a webpage displaying the public posts of its users.
The focus is on providing a working solution to key problems than on
providing the optimal solution.

An example of a feed is available at [@release](https://dev.bovine.social/@release).
The current scope is:

- Display actor and posts
- Correct redirecting behavior for easy use
- Display replies (todo)
- Export
- Import from compatible sources (todo)

This is not an independent solution. It relies on both the [context](./context.md) and
[simple_storage](./simple_storage.md) extension of cattle_grid.
"""

import json
import logging
from uuid import uuid4

from bovine.activitystreams.utils import is_public
from sqlalchemy import select

from muck_out.cattle_grid import ParsedActivity, ParsedEmbeddedObject
from uuid6 import uuid7

from cattle_grid.account.account import account_for_actor
from cattle_grid.dependencies import (
    AccountExchangePublisher,
    ActivityExchangePublisher,
    CommittingSession,
    SqlSession,
)
from cattle_grid.dependencies.processing import FactoriesForActor

from cattle_grid.extensions.examples.html_display.storage import object_for_object_id
from cattle_grid.manage.actor import ActorManager
from cattle_grid.model import ActivityMessage
from cattle_grid.model.exchange import UpdateActorMessage
from cattle_grid.model.exchange_update_actor import UpdateActionType, UpdateUrlAction
from cattle_grid.activity_pub.activity import actor_deletes_themselves

from .dependencies import PublishingActor
from .publisher import Publisher

from .database import (
    ExportPermission,
    PublishedObject,
    PublishedObjectInteraction,
    PublishingActor as DBPublishingActor,
)
from .router import router
from .types import ExportTokenResponse, InteractionType, NameActorMessage
from .extension_declaration import extension

logger = logging.getLogger(__name__)


extension.include_router(router)


@extension.subscribe("html_display_publish_object")
async def html_publish_object(
    message: ActivityMessage,
    session: CommittingSession,
    publishing_actor: PublishingActor,
    config: extension.Config,  # type:ignore
    factories: FactoriesForActor,
    activity_publisher: ActivityExchangePublisher,
):
    """Publishes an object"""
    obj = message.data

    if not is_public(obj):
        await activity_publisher(
            ActivityMessage(actor=message.actor, data=obj),
            routing_key="publish_object",
        )
        return

    if obj.get("id"):
        raise ValueError("Object ID must not be set")

    if obj.get("attributedTo") != message.actor:
        raise ValueError("Actor must match object attributedTo")

    publisher = Publisher(publishing_actor, config, obj)
    session.add(
        PublishedObject(
            id=publisher.uuid,
            data=publisher.object_for_store,
            actor=publishing_actor.actor,
        )
    )

    activity = factories[0].create(publisher.object_for_remote).build()

    await activity_publisher(
        ActivityMessage(actor=message.actor, data=activity),
        routing_key="publish_activity",
    )


@extension.subscribe("html_display_name")
async def name_actor(
    message: NameActorMessage,
    publishing_actor: PublishingActor,
    session: CommittingSession,
    activity_publisher: ActivityExchangePublisher,
    config: extension.Config,  # type:ignore
):
    """Sets the display name of the actor"""
    if message.actor != publishing_actor.actor:
        raise Exception("Actor mismatch")

    publishing_actor.name = message.name

    await activity_publisher(
        UpdateActorMessage(
            actor=publishing_actor.actor,
            actions=[
                UpdateUrlAction(
                    action=UpdateActionType.add_url,
                    url=config.html_url(publishing_actor.actor, publishing_actor.name),
                    media_type="text/html",
                )
            ],
        ),
        routing_key="update_actor",
    )

    if config.automatically_add_users_to_group:
        manager = ActorManager(actor_id=publishing_actor.actor, session=session)
        await manager.add_to_group("html_display")


@extension.subscribe("html_display_export", replies=True)
async def export_create_token(
    publishing_actor: PublishingActor,
    session: CommittingSession,
    publisher: AccountExchangePublisher,
    config: extension.Config,  # type:ignore
):
    """Provides a token and download link for the export of stored objects

    The response is of type [cattle_grid.extensions.examples.html_display.types.ExportTokenResponse][] and
    send to `receive.NAME.response.trigger`."""
    token_uuid = uuid4()
    session.add(
        ExportPermission(publishing_actor=publishing_actor, one_time_token=token_uuid)
    )

    account = await account_for_actor(session, publishing_actor.actor)

    if not account:
        raise Exception("Could not find account")

    await publisher(
        ExportTokenResponse(
            actor=publishing_actor.actor,
            token=str(token_uuid),
            export_url=config.html_url(publishing_actor.actor, publishing_actor.name)
            + f"/export?token={str(token_uuid)}",
        ),
        routing_key=f"receive.{account.name}.response.trigger",
    )


@extension.subscribe("outgoing.Delete")
async def outgoing_delete(
    message: ActivityMessage,
    session: SqlSession,
):
    """Deletes the publishing actor, if they delete themself"""
    activity = message.data.get("raw")
    if not isinstance(activity, dict):
        return
    if not actor_deletes_themselves(activity):
        return

    actor = await session.scalar(
        select(DBPublishingActor).where(DBPublishingActor.actor == message.actor)
    )
    if not actor:
        return

    logger.info("Deleting publishing actor with name %s", actor.name)

    await session.delete(actor)
    await session.flush()


@extension.subscribe("incoming.Like")
async def html_display_incoming_like(
    activity: ParsedActivity,
    message: ActivityMessage,
    session: CommittingSession,
):
    """Handles likes"""
    if activity is None:
        logger.info("Unparsed like: " + json.dumps(message.data, indent=2))
        return
    object_id = activity.object

    if not isinstance(object_id, str):
        return

    published_object = await object_for_object_id(session, object_id)

    session.add(
        PublishedObjectInteraction(
            id=uuid7(),
            published_object=published_object,
            object_id=activity.id,
            interaction=InteractionType.likes,
        )
    )


@extension.subscribe("incoming.Announce")
async def html_display_incoming_announce(
    activity: ParsedActivity,
    message: ActivityMessage,
    session: CommittingSession,
):
    """Handles announces"""
    if activity is None:
        logger.info("Unparsed announce: " + json.dumps(message.data, indent=2))
        return
    object_id = activity.object

    if not isinstance(object_id, str):
        return

    published_object = await object_for_object_id(session, object_id)

    session.add(
        PublishedObjectInteraction(
            id=uuid7(),
            published_object=published_object,
            object_id=activity.id,
            interaction=InteractionType.shares,
        )
    )


@extension.subscribe("incoming.Create")
async def html_display_incoming_create(
    embedded_object: ParsedEmbeddedObject,
    session: CommittingSession,
):
    """Handles replies"""
    if not embedded_object:
        return

    object_id = embedded_object.in_reply_to

    if not isinstance(object_id, str):
        return

    published_object = await object_for_object_id(session, object_id)

    session.add(
        PublishedObjectInteraction(
            id=uuid7(),
            published_object=published_object,
            object_id=embedded_object.id,
            interaction=InteractionType.replies,
        )
    )
