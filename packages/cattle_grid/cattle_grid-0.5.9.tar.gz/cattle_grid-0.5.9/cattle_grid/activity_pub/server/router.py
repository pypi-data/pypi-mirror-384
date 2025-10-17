"""ActivityPub related functionality"""

import logging
from fastapi import APIRouter, HTTPException

from bovine.activitystreams import OrderedCollection
from bovine.activitystreams.utils import as_list
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from cattle_grid.database.activity_pub_actor import Actor
from cattle_grid.dependencies.fastapi import SqlSession

from cattle_grid.activity_pub.actor import (
    actor_to_object,
)
from cattle_grid.activity_pub.actor.relationship import (
    followers_for_actor,
    following_for_actor,
)
from cattle_grid.tools.fastapi import ActivityResponse, ActivityPubHeaders

from .validate import validate_request

logger = logging.getLogger(__name__)

ap_router = APIRouter()


def extract_html_url(actor: Actor) -> str | None:
    urls = as_list(actor.profile.get("url", []))

    for url in urls:
        if isinstance(url, str):
            return url
        if url.get("mediaType").startswith("text/html"):
            return url.get("href")

    return None


@ap_router.get("/actor/{id_str}", response_class=ActivityResponse)
async def actor_profile(headers: ActivityPubHeaders, session: SqlSession):
    """Returns the actor"""
    logger.debug("Request for actor at %s", headers.x_ap_location)
    actor = await session.scalar(
        select(Actor)
        .where(Actor.actor_id == headers.x_ap_location)
        .options(joinedload(Actor.identifiers))
    )

    if headers.x_cattle_grid_should_serve == "html":
        if not actor:
            raise HTTPException(404)
        html_url = extract_html_url(actor)
        if html_url:
            return RedirectResponse(html_url)
        raise HTTPException(406)

    actor = await validate_request(session, actor, headers.x_cattle_grid_requester)

    result = actor_to_object(actor)
    return result


@ap_router.get("/outbox/{id_str}", response_class=ActivityResponse)
async def outbox(headers: ActivityPubHeaders, session: SqlSession):
    """Returns an empty ordered collection as outbox"""
    actor = await session.scalar(
        select(Actor).where(Actor.outbox_uri == headers.x_ap_location)
    )
    actor = await validate_request(session, actor, headers.x_cattle_grid_requester)

    return OrderedCollection(id=headers.x_ap_location).build()


@ap_router.get("/following/{id_str}", response_class=ActivityResponse)
async def following(id_str, headers: ActivityPubHeaders, session: SqlSession):
    """Returns the following"""

    actor = await session.scalar(
        select(Actor).where(Actor.following_uri == headers.x_ap_location)
    )
    actor = await validate_request(session, actor, headers.x_cattle_grid_requester)

    following = await following_for_actor(session, actor)
    return OrderedCollection(id=headers.x_ap_location, items=list(following)).build()


@ap_router.get("/followers/{id_str}", response_class=ActivityResponse)
async def followers(id_str, headers: ActivityPubHeaders, session: SqlSession):
    """Returns the followers"""
    actor = await session.scalar(
        select(Actor).where(Actor.followers_uri == headers.x_ap_location)
    )
    actor = await validate_request(session, actor, headers.x_cattle_grid_requester)

    followers = await followers_for_actor(session, actor)
    return OrderedCollection(id=headers.x_ap_location, items=list(followers)).build()
