import asyncio
from behave import given, then, when

from cattle_grid.extensions.examples.html_display.types import NameActorMessage


@given('"{alice}" sets her display name to "{alex}"')  # type: ignore
async def html_set_display_name(context, alice, alex):
    connection = context.connections[alice]
    alice_id = context.actors[alice].get("id")

    await connection.trigger(
        "html_display_name", NameActorMessage(actor=alice_id, name=alex).model_dump()
    )

    await asyncio.sleep(0.2)


@then("The profile contains an url")  # type: ignore
def profile_contains_url(context):
    urls = context.profile.get("url")

    assert isinstance(urls, list)
    assert len(urls) >= 1


@when('"{alice}" requests an export token')  # type: ignore
async def request_token(context, alice):
    connection = context.connections[alice]
    alice_id = context.actors[alice].get("id")

    context.export_response = await connection.trigger(
        "html_display_export", {"actor": alice_id}
    )

    assert "token" in context.export_response


@when("The export url is retrieved")  # type: ignore
async def step_impl(context):
    async with context.session.get(
        context.export_response["export_url"],
    ) as response:
        context.response = response
        context.response_content = await response.text()


@then('The response contains "{text}"')  # type: ignore
async def response_contains(context, text):
    content = context.response_content
    assert text in content, f"Got content: {content}"


@then('A request to the object using accept "{media_type}" gets redirected')  # type: ignore
async def is_redirected(context, media_type):
    async with context.session.get(
        context.media_type_link,
        headers={"accept": media_type},
        allow_redirects=False,
    ) as response:
        assert response.status >= 300 and response.status < 400, (
            f"{response.status} is not a redirect"
        )
