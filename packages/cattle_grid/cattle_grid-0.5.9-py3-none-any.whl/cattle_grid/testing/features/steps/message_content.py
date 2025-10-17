"""Routines to check the content of a message as retrieved by
[cattle_grid.testing.features.steps.messaging.receive_message][]"""

from behave import then

from bovine.activitystreams.utils import as_list


@then('The received message contains an URL of mediatype "{media_type}"')  # pyright: ignore[reportCallIssue]
def message_contains_url_of_mediatype(context, media_type):
    """

    ```gherkin
    Then The received message contains an URL of mediatype "text/html"
    ```

    The resolved url is added to `context.media_type_link`.
    """

    message = context.received_object

    urls = as_list(message.get("url", []))

    html_url = next(
        (x for x in urls if isinstance(x, dict) and x.get("mediaType") == media_type),
        None,
    )
    assert html_url

    assert html_url.get("type") == "Link"
    assert html_url.get("href")

    context.media_type_link = html_url.get("href")


@then('The URL resolves to a webpage containing "{text}"')  # pyright: ignore[reportCallIssue]
async def step_impl(context, text):
    """
    ```gherkin
    Then The URL resolves to a webpage
    ```
    """

    async with context.session.get(
        context.media_type_link, headers={"accept": "text/html"}
    ) as response:
        assert response.status == 200, (
            f"Status is {response.status} != 200 for {context.media_type_link}"
        )
        content_type = response.headers["content-type"]
        assert content_type.startswith("text/html"), (
            f"Got response content-type {content_type}"
        )

        content = await response.text()

        assert text in content, f"Content {content} does not contain {text}"
