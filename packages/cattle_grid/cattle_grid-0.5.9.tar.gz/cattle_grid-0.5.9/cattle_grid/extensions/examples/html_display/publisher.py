from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from bovine.activitystreams.utils import as_list
from uuid6 import uuid7


from .config import HtmlDisplayConfiguration
from .database import PublishingActor


@dataclass
class Publisher:
    """Class for manipulating objects being published"""

    actor: PublishingActor
    config: HtmlDisplayConfiguration
    obj: dict[str, Any]
    uuid: UUID = field(default_factory=uuid7)

    def __post_init__(self):
        if "id" in self.obj:
            obj_id = self.obj["id"]
            self.uuid = UUID(obj_id.split("/")[-1])
        else:
            self.obj = {
                **self.obj,
                "id": self.config.url_start(self.actor.actor) + str(self.uuid),
            }

    @property
    def object_for_store(self):
        return self.obj

    @property
    def object_for_remote(self):
        copy = {**self.obj}
        copy.update(self._collection_links())
        return self._add_url_to_obj(copy)

    def _collection_links(self):
        object_id = self.obj["id"]
        return {
            collection: f"{object_id}/{collection}"
            for collection in ["replies", "shares", "likes"]
        }

    def _add_url_to_obj(self, obj: dict):
        url_list = as_list(obj.get("url", []))

        url = (
            self.config.html_url_start(self.actor.actor)
            + self.actor.name
            + "/o/"
            + str(self.uuid)
        )

        obj["url"] = url_list + [self.create_html_link(url)]

        return obj

    def create_html_link(self, url: str | None = None):
        if url is None:
            url = self.actor.actor_id + "#html"
        return {"type": "Link", "mediaType": "text/html", "href": url}
