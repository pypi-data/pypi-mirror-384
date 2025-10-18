import re
import pytest

from muck_out.types import Actor
from muck_out.types.validated.actor import PropertyValue

from muck_out.testing.examples import mitra_actor, actor_example

from .actor import normalize_property_value, normalize_actor, actor_stub


def test_normalize_actor_failure():
    assert normalize_actor({}) is None


actor_base = {
    "@context": "https://www.w3.org/ns/activitystreams",
    "type": "Person",
    "id": "https://example.com/users/alice",
}


@pytest.mark.parametrize(
    "data",
    [
        {
            "@context": "https://www.w3.org/ns/activitystreams",
            "type": "Person",
            "id": "https://example.com/users/alice",
            "inbox": "https://example.com/users/alice/inbox",
        },
        {
            "@context": "https://www.w3.org/ns/activitystreams",
            "type": "Person",
            "id": "https://example.com/users/alice",
            "inbox": "https://example.com/users/alice/inbox",
            "icon": {
                "type": "Image",
                "url": "https://example.com/users/alice/icon.png",
            },
        },
    ],
)
def test_normalize_actor(data):
    assert isinstance(normalize_actor(data), Actor)


def to_snake_case(string: str):
    return re.sub("([A-Z]+)", r"_\1", string).lower()


@pytest.mark.parametrize(
    "field, value, mapped",
    [
        ("summary", "<p>Hello, world!</p>", "<p>Hello, world!</p>"),
        (
            "summary",
            "<p>Test<script>alert('hi')</script></p>",
            "<p>Test</p>",
        ),
        ("name", "Alice", "Alice"),
        (
            "alsoKnownAs",
            ["https://example.com/users/alice"],
            ["https://example.com/users/alice"],
        ),
    ],
)
def test_normalize_actor_field(field: str, value: str, mapped: str):
    data = actor_base.copy()
    data[field] = value
    actor = actor_stub(data)
    assert getattr(actor, to_snake_case(field)) == mapped


def test_actor_import():
    result = actor_stub(mitra_actor)

    assert result.url
    assert result.preferred_username == "admin"
    assert result.identifiers == ["acct:admin@mitra", "http://mitra/users/admin"]

    assert result.following == mitra_actor["following"]
    assert result.followers == mitra_actor["followers"]

    assert result.url == [
        {
            "href": "http://mitra/users/admin",
            "type": "Link",
        },
    ]


def test_actor_import_icon():
    result = actor_stub(actor_example)

    assert result.icon


def test_normalize_property_value_dict():
    data = {"type": "Other", "name": "wooo"}

    assert normalize_property_value(data) == data


def test_normalize_property_value():
    data = {
        "type": "PropertyValue",
        "name": "Blog",
        "value": '<a href="http://value.example/" target="_blank" rel="nofollow noopener noreferrer me" translate="no"><span class="invisible">http://</span><span class="">value.example/</span><span class="invisible"></span></a>',
    }

    result = normalize_property_value(data)

    assert isinstance(result, PropertyValue)

    assert result.value == "http://value.example/"
