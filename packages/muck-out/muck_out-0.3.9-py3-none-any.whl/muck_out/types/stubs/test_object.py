import pytest

from . import ObjectStub


@pytest.mark.parametrize(
    "url,expected",
    [
        ("http://remote.test", [{"type": "Link", "href": "http://remote.test"}]),
        (["http://remote.test"], [{"type": "Link", "href": "http://remote.test"}]),
        (
            [{"type": "Link", "href": "http://remote.test"}],
            [{"type": "Link", "href": "http://remote.test"}],
        ),
        (
            {"type": "Link", "href": "http://remote.test"},
            [{"type": "Link", "href": "http://remote.test"}],
        ),
        (
            ["http://one.test", {"type": "Link", "href": "http://two.test"}],
            [
                {"type": "Link", "href": "http://one.test"},
                {"type": "Link", "href": "http://two.test"},
            ],
        ),
    ],
)
def test_object_stub_url(url, expected):
    stub = ObjectStub(url=url)  # type:ignore

    assert stub.url == expected


def test_object_stub_content():
    stub = ObjectStub(content="content")  # type:ignore

    assert stub.content == "content"


def test_object_parse_emoji():
    data = {
        "type": "Note",
        "attributedTo": "http://actor.example",
        "to": ["https://www.w3.org/ns/activitystreams#Public"],
        "id": "http://actor.example/object/gGhtmEsRxq0",
        "published": "2025-09-09T09:32:39Z",
        "content": "emoji just id :cow:",
        "tag": ["http://pasture-one-actor/assets/cow_emoji.jsonap"],
        "@context": [
            "https://www.w3.org/ns/activitystreams",
            {"Hashtag": "as:Hashtag", "sensitive": "as:sensitive"},
        ],
    }

    stub = ObjectStub.model_validate(data)

    assert stub.tag == [{"href": "http://pasture-one-actor/assets/cow_emoji.jsonap"}]


def test_object_stub_parse_null_url():
    data = {"url": None}
    ObjectStub.model_validate(data)
