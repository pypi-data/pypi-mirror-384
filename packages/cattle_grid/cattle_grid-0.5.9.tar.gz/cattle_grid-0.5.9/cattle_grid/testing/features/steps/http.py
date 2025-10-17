from behave import when, then


@when('The request URL is the actor object of "{alice}"')  # type: ignore
def request_url_is_actor(context, alice):
    alice_obj = context.actors[alice]
    context.request = {"url": alice_obj.get("id")}


@when('The request requests the content-type "{content_type}"')  # type: ignore
def request_set_content_type(context, content_type):
    context.request["content_type"] = content_type


@when("The request is made")  # type: ignore
async def make_request(context):
    async with context.session.get(
        context.request["url"],
        headers={"accept": context.request["content_type"]},
    ) as response:
        context.response = response


@then('The response code is "{status_code}"')  # type: ignore
def check_response_status_code(context, status_code):
    assert context.response.status == int(status_code)


@then("The response is a webpage")  # type: ignore
def response_is_webpage(context):
    print(context.response)

    headers = context.response.headers

    assert headers.get("content-type").startswith("text/html"), (
        f"Got content-type {headers.get('content-type')}"
    )
