from sqlalchemy.orm.attributes import flag_modified

from bovine.activitystreams.utils import as_list

from cattle_grid.database.activity_pub_actor import Actor
from cattle_grid.model.exchange_update_actor import UpdateUrlAction


def build_link_for_action(action: UpdateUrlAction):
    result = {"type": "Link", "href": action.url}
    if action.media_type:
        result["mediaType"] = action.media_type
    if action.rel:
        result["rel"] = action.rel

    return result


def url_matches(item: str | dict, url: str) -> bool:
    """Checks if the item represents the url
    ```
    >>> url_matches("http://remote.test", "http://remote.test")
    True

    >>> url_matches({"href": "http://remote.test"}, "http://remote.test")
    True

    ```
    """
    if isinstance(item, dict):
        return item.get("href") == url

    return item == url


def add_url(actor: Actor, action: UpdateUrlAction):
    urls = as_list(actor.profile.get("url", []))
    urls = [url for url in urls if not url_matches(url, action.url)]

    urls.append(build_link_for_action(action))
    actor.profile["url"] = urls

    flag_modified(actor, "profile")


def remove_url(actor: Actor, action: UpdateUrlAction):
    urls = as_list(actor.profile.get("url", []))

    actor.profile["url"] = [url for url in urls if not url_matches(url, action.url)]
    flag_modified(actor, "profile")
