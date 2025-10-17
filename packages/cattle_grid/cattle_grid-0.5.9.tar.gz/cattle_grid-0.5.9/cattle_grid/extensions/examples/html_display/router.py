import logging
from uuid import UUID
from bovine.activitystreams import OrderedCollection
import jinja2
from fastapi.templating import Jinja2Templates

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select

from muck_out.transform.utils import sanitize_html

from cattle_grid.activity_pub import is_valid_requester_for_obj
from cattle_grid.dependencies.fastapi import SqlSession
from cattle_grid.extensions.examples.html_display.format import format_actor_profile
from cattle_grid.extensions.examples.html_display.database import (
    ExportPermission,
    PublishedObject,
    PublishingActor,
)
from cattle_grid.extensions.examples.html_display.publisher import Publisher
from cattle_grid.extensions.examples.html_display.types import InteractionType
from cattle_grid.tools.fastapi import (
    ActivityPubHeaders,
    ActivityResponse,
    ShouldServe,
    ContentType,
)

from cattle_grid.version import __version__

from .fastapi_dependencies import (
    ActorProfile,
    PublishedObjectForUUID,
    PublishedObjectWithInteractionsForUUID,
    PublishingActorForName,
)
from .extension_declaration import extension

logger = logging.getLogger(__name__)

templates = Jinja2Templates(
    env=jinja2.Environment(auto_reload=True, loader=jinja2.PackageLoader(__name__)),
)

router = APIRouter()


@router.get("/")
async def get_index():
    """Dummy index page, only useful for debugging"""
    return "html extension"


@router.get("/object/{uuid}", response_class=ActivityResponse, tags=["activity_pub"])
async def get_object(
    obj: PublishedObjectForUUID,
    ap_headers: ActivityPubHeaders,
    session: SqlSession,
    config: extension.ConfigFastAPI,  # type:ignore
):
    """Returns the stored object"""
    if not ap_headers.x_cattle_grid_requester:
        raise HTTPException(401)

    if ap_headers.x_ap_location != obj.data.get("id"):
        raise HTTPException(404)

    if not await is_valid_requester_for_obj(
        session, ap_headers.x_cattle_grid_requester, obj.data
    ):
        raise HTTPException(401)

    actor = await session.scalar(
        select(PublishingActor).where(PublishingActor.actor == obj.actor)
    )
    if actor is None:
        raise HTTPException(404)

    publisher = Publisher(actor, config, obj=obj.data)

    return publisher.object_for_remote


@router.get(
    "/object/{uuid}/{interaction}",
    response_class=ActivityResponse,
    tags=["activity_pub"],
)
async def get_object_interaction(
    obj: PublishedObjectWithInteractionsForUUID,
    ap_headers: ActivityPubHeaders,
    session: SqlSession,
    interaction: InteractionType,
):
    """Returns the stored object"""
    if not ap_headers.x_cattle_grid_requester:
        raise HTTPException(401)

    collection_id = f"{obj.data.get('id')}/{interaction}"

    if ap_headers.x_ap_location != collection_id:
        raise HTTPException(404)

    if not await is_valid_requester_for_obj(
        session, ap_headers.x_cattle_grid_requester, obj.data
    ):
        raise HTTPException(401)

    logger.info(obj.interactions)

    return OrderedCollection(
        id=collection_id,
        items=[x.object_id for x in obj.interactions if x.interaction == interaction],
    ).build()


@router.get("/html/{actor_name}", response_class=HTMLResponse, tags=["html"])
@router.get("/html/{actor_name}/", response_class=HTMLResponse, tags=["html"])
async def get_actor_html(
    actor: PublishingActorForName,
    profile: ActorProfile,
    request: Request,
    session: SqlSession,
    should_serve: ShouldServe,
):
    """Returns the HTML representation of the actor"""

    if (
        ContentType.html not in should_serve
        and ContentType.activity_pub in should_serve
    ):
        return RedirectResponse(profile["id"])

    published_objects = await session.scalars(
        select(PublishedObject)
        .where(PublishedObject.actor == actor.actor)
        .order_by(PublishedObject.create_date.desc())
        .limit(10)
    )

    posts = [
        {
            "body": sanitize_html(x.data.get("content")),
            "date": x.data.get("published"),
            "id": str(x.id),
        }
        for x in published_objects
    ]

    return templates.TemplateResponse(
        request,
        name="index.html.j2",
        context={
            "name": actor.name,
            "profile": format_actor_profile(profile),
            "posts": posts,
            "version": __version__,
        },
    )


@router.get("/html/{actor_name}/export", tags=["html"])
async def export_objects(
    actor: PublishingActorForName, token: str, session: SqlSession
):
    """Returns the export of user data, a token needs to be provided.
    The token can be requested via the `html_display_export` method."""
    try:
        token_uuid = UUID(token)
    except ValueError:
        raise HTTPException(422, detail="Invalid uuid as token")

    permission = await session.scalar(
        select(ExportPermission)
        .where(ExportPermission.publishing_actor == actor)
        .where(ExportPermission.one_time_token == token_uuid)
    )

    if not permission:
        raise HTTPException(401)

    items = await session.scalars(
        select(PublishedObject.data).where(PublishedObject.actor == actor.actor)
    )

    return OrderedCollection(id="objects.json", items=items.all()).build()  # type: ignore


@router.get("/html/{actor_name}/o/{uuid}", response_class=HTMLResponse, tags=["html"])
@router.get(
    "/html/{actor_name}/{uuid}",
    response_class=HTMLResponse,
    deprecated=True,
    tags=["html"],
)
async def get_object_html(
    actor: PublishingActorForName,
    obj: PublishedObjectWithInteractionsForUUID,
    request: Request,
    should_serve: ShouldServe,
):
    """Returns the HTML representation for an object"""
    if actor.actor != obj.actor:
        raise HTTPException(404)

    if (
        ContentType.html not in should_serve
        and ContentType.activity_pub in should_serve
    ):
        return RedirectResponse(obj.data["id"])

    interactions = {
        str(interaction): [
            x.object_id for x in obj.interactions if x.interaction == interaction
        ]
        for interaction in [
            InteractionType.shares,
            InteractionType.likes,
            InteractionType.replies,
        ]
    }

    return templates.TemplateResponse(
        request,
        name="object.html.j2",
        context={
            "name": actor.name,
            "content": sanitize_html(obj.data["content"]),
            **interactions,
            "version": __version__,
        },
    )
