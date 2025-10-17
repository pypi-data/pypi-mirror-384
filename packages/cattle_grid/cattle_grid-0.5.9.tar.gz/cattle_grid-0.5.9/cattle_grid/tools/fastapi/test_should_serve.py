from unittest.mock import AsyncMock
from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from .http_util import ContentType
from . import ShouldServe


@pytest.mark.parametrize(
    "headers,expected",
    [
        ({}, [ContentType.other]),
        ({"accept": "text/html"}, [ContentType.html]),
        ({"accept": "text/html; charsed=utf-8"}, [ContentType.html]),
        ({"accept": "application/activity+json"}, [ContentType.activity_pub]),
    ],
)
async def test_should_serve(headers, expected):
    mock = AsyncMock()
    app = FastAPI()

    @app.get("/")
    async def serve(should_serve: ShouldServe):
        await mock(should_serve)

    client = TestClient(app, headers=headers)

    client.get("/")
    mock.assert_awaited_once_with(expected)
