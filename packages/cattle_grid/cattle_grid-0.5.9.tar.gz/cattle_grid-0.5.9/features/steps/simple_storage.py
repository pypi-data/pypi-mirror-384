import asyncio
from behave import when, then

from bovine.activitystreams import factories_for_actor_object

from cattle_grid.testing.features import publish_as, fetch_request


@when('"{alice}" publishes a "{moo}" animal sound to her followers')  # pyright: ignore[reportCallIssue]
async def send_sound(context, alice, moo):
    for connection in context.connections.values():
        await connection.clear_incoming()

    alice_actor = context.actors[alice]
    activity_factory, _ = factories_for_actor_object(alice_actor)

    activity = (
        activity_factory.custom(type="AnimalSound", content="moo").as_public().build()
    )

    await publish_as(
        context,
        alice,
        "publish_activity",
        {"actor": context.actors[alice].get("id"), "data": activity},
    )


@when('"{alice}" publishes a message "{text}" to her followers')  # pyright: ignore[reportCallIssue]
async def send_message(context, alice, text):
    await asyncio.sleep(0.3)
    for connection in context.connections.values():
        await connection.clear_incoming()

    alice_actor = context.actors[alice]
    _, object_factory = factories_for_actor_object(alice_actor)

    note = object_factory.note(content=text).as_public().build()

    await publish_as(
        context,
        alice,
        "publish_object",
        {"actor": context.actors[alice].get("id"), "data": note},
    )


@then('"{bob}" can retrieve the activity')  # pyright: ignore[reportCallIssue]
async def can_retrieve_activity(context, bob):
    result = await fetch_request(context, bob, context.activity.get("id"))
    assert result
