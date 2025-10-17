from behave import then, when, given
from cattle_grid.testing.features import fetch_request


@when('"{actor}" retrieves the object with the actor id of "{target}"')  # pyright: ignore[reportCallIssue]
async def retrieve_object(context, actor, target):
    context.result = await fetch_request(
        context,
        actor,
        context.actors[target].get("id"),
    )


@when('"{actor}" retrieves the object with id "{uri}"')  # pyright: ignore[reportCallIssue]
async def retrieve_object_by_uri(context, actor, uri):
    context.result = await fetch_request(
        context,
        actor,
        uri,
    )


@then('The retrieved object is the profile of "{username}"')  # pyright: ignore[reportCallIssue]
def check_result_is_actor(context, username):
    assert context.result.get("type") == "Person"
    assert context.result.get("id") == context.actors[username].get("id")


@then("no result is returned")  # type: ignore
def no_result(context):
    assert context.result is None


@given('"Alice" has messaged "Bob"')  # type: ignore
def step_impl(context):
    context.execute_steps(
        """
        When "Alice" sends "Bob" a message saying "Hello Bob"
        Then "Bob" receives a message saying "Hello Bob"
    """
    )
