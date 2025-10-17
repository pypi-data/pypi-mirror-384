import json

from behave import when, then


@when('"{alice}" sends the trigger action "{method}" with content')  # type: ignore
async def alice_triggers(context, alice, method):
    text_content = context.text
    text_content = text_content.replace(
        f"__{alice}_ID__", context.actors[alice].get("id")
    )

    print()
    print(text_content)
    print()

    await context.connections[alice].trigger(method, json.loads(text_content))


@then('"{alice}" receives an error')  # type: ignore
async def alice_receives_an_error(context, alice):
    error = await context.connections[alice].next_error()

    assert error
