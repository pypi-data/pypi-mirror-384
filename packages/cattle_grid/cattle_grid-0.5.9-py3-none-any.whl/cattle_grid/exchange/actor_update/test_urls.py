from copy import deepcopy
from cattle_grid.testing.fixtures import *  # noqa
from cattle_grid.model.exchange_update_actor import UpdateUrlAction, UpdateActionType

from .urls import add_url, remove_url


def test_handle_add_url(actor_for_test):
    url = "http://local.test/html/page"
    add_url(
        actor_for_test,
        UpdateUrlAction(
            action=UpdateActionType.add_url, url=url, media_type="text/html"
        ),
    )

    urls = actor_for_test.profile.get("url", [])

    assert len(urls) >= 1

    assert urls[-1] == {"type": "Link", "href": url, "mediaType": "text/html"}


def test_handle_add_url_is_idempotent(actor_for_test):
    url = "http://local.test/html/page"
    add_url(
        actor_for_test,
        UpdateUrlAction(
            action=UpdateActionType.add_url, url=url, media_type="text/html"
        ),
    )

    urls = deepcopy(actor_for_test.profile.get("url", []))

    add_url(
        actor_for_test,
        UpdateUrlAction(
            action=UpdateActionType.add_url, url=url, media_type="text/html"
        ),
    )

    urls_again = actor_for_test.profile.get("url", [])

    assert urls == urls_again


def test_handle_remove_url(actor_for_test):
    url = "http://local.test/html/page"
    add_url(
        actor_for_test,
        UpdateUrlAction(
            action=UpdateActionType.add_url, url=url, media_type="text/html"
        ),
    )
    remove_url(
        actor_for_test,
        UpdateUrlAction(action=UpdateActionType.remove_url, url=url),
    )

    urls = actor_for_test.profile.get("url", [])

    assert len(urls) == 0
