import logging
from behave import given, when

from cattle_grid.config import load_settings
from cattle_grid.database import database_session
from cattle_grid.manage.actor import ActorManager
from cattle_grid.model.exchange import UpdateActorMessage

from cattle_grid.testing.features import publish_as, fetch_request

logger = logging.getLogger(__name__)


@given('A new user called "{username}" on "{hostname}"')  # pyright: ignore[reportCallIssue]
def new_user_on_server(context, username, hostname):
    context.execute_steps(
        f"""
        Given An account called "{username}"
        Given "{username}" created an actor on "{hostname}" called "{username}"
        """
    )


@given('A new user called "{username}"')  # pyright: ignore[reportCallIssue]
def new_user(context, username):
    """Creates a new user

    Usage example:

    ```gherkin
    Given A new user called "Alice"
    ```
    """
    hostname = {"alice": "abel", "bob": "banach", "Bob": "banach"}.get(username, "abel")

    context.execute_steps(
        f"""
        Given A new user called "{username}" on "{hostname}"
        """
    )


@when('"{alice}" updates her profile')  # pyright: ignore[reportCallIssue]
async def update_profile(context, alice):
    """
    ```gherkin
    When "Alice" updates her profile
    ```
    """

    for connection in context.connections.values():
        await connection.clear_incoming()

    alice_id = context.actors[alice].get("id")

    msg = UpdateActorMessage(
        actor=alice_id, profile={"summary": "I love cows"}
    ).model_dump()

    await publish_as(context, alice, "update_actor", msg)


@when('"{alice}" fetches her profile')  # pyright: ignore[reportCallIssue]
async def fetch_profile(context, alice):
    """
    ```gherkin
    When "Alice" fetches her profile
    ```

    The profile is stored in `context.profile`
    """

    alice_id = context.actors[alice].get("id")

    context.profile = await fetch_request(context, alice, alice_id)

    assert isinstance(context.profile, dict)


@when('"{alice}" deletes herself')  # pyright: ignore[reportCallIssue]
@when('"{alice}" deletes himself')  # pyright: ignore[reportCallIssue]
async def actor_deletes_themselves(context, alice):
    """
    ```gherkin
    When "Alice" deletes herself
    When "Bob" deletes himself
    ```
    """
    alice_id = context.actors[alice].get("id")

    await publish_as(
        context,
        alice,
        "delete_actor",
        {
            "actor": alice_id,
        },
    )


@given('"{alice}" is in the "{group_name}" group')  # pyright: ignore[reportCallIssue]
async def in_group(context, alice, group_name):
    """
    ```gherkin
    And "Alice" is in the "html" group
    ```
    """
    alice_id = context.actors[alice].get("id")
    config = load_settings()

    async with database_session(db_uri=config.get("db_uri")) as session:  # type: ignore
        manager = ActorManager(session=session, actor_id=alice_id)

        await manager.add_to_group(group_name)
