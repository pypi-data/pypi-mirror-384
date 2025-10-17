from typing import Annotated

from fast_depends import Depends
from cattle_grid.dependencies import CommittingSession
from cattle_grid.dependencies.processing import MessageActor

from .storage import publishing_actor_for_actor_id
from .database import PublishingActor as PublishingActorModel


async def publishing_actor(session: CommittingSession, actor: MessageActor):
    # FIXME: Should one at this point require the actor to be part
    # of the html_display group.
    # If yes, how should this be configured?

    return await publishing_actor_for_actor_id(session, actor.actor_id)


PublishingActor = Annotated[PublishingActorModel, Depends(publishing_actor)]
"""Returns the publishing actor"""
