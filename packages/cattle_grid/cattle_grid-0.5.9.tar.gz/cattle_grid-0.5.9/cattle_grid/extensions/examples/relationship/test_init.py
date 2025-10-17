import pytest
from cattle_grid.extensions.load import build_transformer

from cattle_grid.testing.fixtures import *  # noqa
from cattle_grid.database.activity_pub_actor import Follower

from muck_out.extension import extension as muck_out
from . import extension


@pytest.fixture
def transformer():
    return build_transformer([muck_out, extension])


@pytest.fixture
def remote_actor_profile():
    return {
        "@context": [
            "https://www.w3.org/ns/activitystreams",
            "http://joinmastodon.org/ns",
            "https://w3id.org/security/v1",
        ],
        "discoverable": False,
        "featured": "http://gotosocial/users/cookie/collections/featured",
        "followers": "http://gotosocial/users/cookie/followers",
        "following": "http://gotosocial/users/cookie/following",
        "id": "http://gotosocial/users/cookie",
        "inbox": "http://gotosocial/users/cookie/inbox",
        "manuallyApprovesFollowers": True,
        "name": "cookie",
        "outbox": "http://gotosocial/users/cookie/outbox",
        "preferredUsername": "cookie",
        "publicKey": {
            "id": "http://gotosocial/users/cookie/main-key",
            "owner": "http://gotosocial/users/cookie",
            "publicKeyPem": "-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA0SwHxmzQTZrdQkiD1a68\nMg4gDbkqAzocxngdjXOG4Y92q2MZB/ByRaPS7ap4e5EKDa3TaVIz0JeoZGytlmMu\ntvBRKfLyutGZLz6hkrlkSGzQT9XGYrmfkrXqCjSq4kML0ncMBpaf+VQPjpiqcBTp\n0N3NZCNp3tfarGeL1+CNJpz6qZI0UsSp3pStrE1+DIQbIay4tlgHdjvX0nBPalen\nVWXxdSgywF1A4mEmdwkSVJ7Jl7pQEGT4q5ojFuAdTcTFMGskUmez8trVTqHNAs9M\n3TmZbtWgNKG/AuYrR1CPkEoup+aCPpjvMR4EWtnqxbTFfmN1DUGepPjVPHzb+UBQ\nRQIDAQAB\n-----END PUBLIC KEY-----\n",
        },
        "tag": [],
        "type": "Person",
        "url": "http://gotosocial/@cookie",
    }


async def test_transformer_with_actor_id(transformer, actor_for_test):
    result = await transformer({"raw": {}}, actor_id=actor_for_test.actor_id)

    assert "relationship" in result
    assert result["relationship"] == {}


async def test_transformer_with_follower(
    transformer, remote_actor_profile, actor_for_test, sql_session
):
    sql_session.add(
        Follower(
            actor=actor_for_test,
            follower=remote_actor_profile["id"],
            accepted=True,
            request=remote_actor_profile["id"] + "#follow_request",
        )
    )

    await sql_session.commit()

    result = await transformer(
        {"raw": remote_actor_profile}, actor_id=actor_for_test.actor_id
    )

    relationship = result["relationship"]

    assert "follower" in relationship
