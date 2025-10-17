import pytest

from .format import format_actor_profile


@pytest.fixture
def profile():
    return {
        "attachment": [
            {
                "type": "PropertyValue",
                "name": "Author",
                "value": "acct:helge@mymath.rocks",
            },
            {
                "type": "PropertyValue",
                "name": "Source",
                "value": "https://codeberg.org/bovine/roboherd",
            },
            {
                "type": "PropertyValue",
                "name": "Frequency",
                "value": "At 42 minutes past the hour",
            },
        ],
        "published": "2025-09-07T12:39:49.096182",
        "@context": [
            "https://www.w3.org/ns/activitystreams",
            "https://w3id.org/security/v1",
            {
                "PropertyValue": {
                    "@id": "https://schema.org/PropertyValue",
                    "@context": {
                        "value": "https://schema.org/value",
                        "name": "https://schema.org/name",
                    },
                }
            },
        ],
        "publicKey": {
            "id": "http://abel/actor/FqHFi7vFmVOalVXogLZmtA#legacy-key-1",
            "owner": "http://abel/actor/FqHFi7vFmVOalVXogLZmtA",
            "publicKeyPem": "-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA4wMPZRHfpDSTL2p0Y/Fo\nZ7VCUYh+f0NUqobOQgwEacdetNwcmgIwYwldu5mpbM5vKlTEac9fYSK6r9yiIj2q\nsds9CvyHXfTeiapI4nYWOtnLzwbW1p4t0FOpcwii6s4flii937CYGVgCmNyB1UR9\nqDbdbJwVUCeO9oixOnt2WWO5EZnBWGpMnCfNtbGiRdFQthCWia+KWMkcle6xSxWk\n+69Xiu4ClH0ma9TfftC4eEZgZ8UQdmLgdOKKysGk+5+jJBClqQwZOjhRWBZtH+Js\nPmV33KKrK5nd0sDqekExXqsJ23UDTVcXywhIBtFy948VSVtlmBM9jX9wzZJ/i8Tf\nqQIDAQAB\n-----END PUBLIC KEY-----\n",
        },
        "id": "http://abel/actor/FqHFi7vFmVOalVXogLZmtA",
        "type": "Service",
        "inbox": "http://abel/inbox/8JF7O5ADRHFaRoHSKVRc9Q",
        "outbox": "http://abel/outbox/iWm7WPxhdWJOC-9CIWArlw",
        "followers": "http://abel/followers/zUK1yGIj0KDI611BK7859g",
        "following": "http://abel/following/Lu7i17EUCg7zWjNjBt-z1A",
        "preferredUsername": "rooster",
        "name": "The crowing rooster \ud83d\udc13",
        "icon": {
            "mediaType": "image/png",
            "type": "Image",
            "url": "https://dev.bovine.social/assets/bull-horns.png",
        },
        "identifiers": [
            "acct:rooster@abel",
            "http://abel/actor/FqHFi7vFmVOalVXogLZmtA",
        ],
        "endpoints": {"sharedInbox": "http://abel/shared_inbox"},
        "summary": "I'm an actor",
    }


def test_format_actor_profile_empty_input():
    format_actor_profile({})


def test_format_actor_profile_fediverse_handles(profile):
    formatted = format_actor_profile(profile)

    assert formatted["fediverse_handles"] == ["@rooster@abel"]


def test_format_actor_profile_summary(profile):
    formatted = format_actor_profile(profile)

    assert formatted["summary"] == "I'm an actor"


def test_format_actor_profile_property_values(profile):
    formatted = format_actor_profile(profile)

    assert formatted["property_values"] == [
        {
            "name": "Author",
            "value": "acct:helge@mymath.rocks",
        },
        {
            "name": "Source",
            "value": "https://codeberg.org/bovine/roboherd",
        },
        {
            "name": "Frequency",
            "value": "At 42 minutes past the hour",
        },
    ]
