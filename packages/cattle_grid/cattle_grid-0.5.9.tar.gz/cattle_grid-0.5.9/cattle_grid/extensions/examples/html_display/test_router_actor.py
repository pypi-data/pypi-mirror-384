from .testing import *  # noqa


def test_get_actor_not_found(test_client):
    response = test_client.get("/html_display/html/alice")
    assert response.status_code == 404


def test_get_actor_found(test_client, publishing_actor_for_test):
    response = test_client.get(f"/html_display/html/{publishing_actor_for_test.name}")
    assert response.status_code == 200


def test_get_actor_redirect_for_activity_pub(test_client, publishing_actor_for_test):
    response = test_client.get(
        f"/html_display/html/{publishing_actor_for_test.name}",
        headers={"accept": "application/activity+json"},
        follow_redirects=False,
    )
    assert response.status_code == 307
    assert response.headers.get("location") == publishing_actor_for_test.actor
