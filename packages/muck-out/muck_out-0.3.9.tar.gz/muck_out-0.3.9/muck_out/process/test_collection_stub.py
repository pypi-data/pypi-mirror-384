import pytest
from muck_out.process.collection import collection_stub


def test_collection_mastodon_outbox_type():
    data = {
        "@context": "https://www.w3.org/ns/activitystreams",
        "id": "http://mastodon.example/users/alice/outbox",
        "type": "OrderedCollection",
        "totalItems": 12360,
        "first": "http://mastodon.example/users/alice/outbox?page=true",
        "last": "http://mastodon.example/users/alice/outbox?min_id=0&page=true",
    }

    result = collection_stub(data)

    assert result.id == data["id"]
    assert result.total_items == data["totalItems"]
    assert result.first == data["first"]
    assert result.last == data["last"]


@pytest.mark.parametrize(
    "data",
    [
        {
            "orderedItems": ["item1", {"aaa": "bbb"}, {"id": "item2"}],
        },
        {
            "items": ["item1", {"aaa": "bbb"}, {"id": "item2"}],
        },
    ],
)
def test_mastodon_outbox_page_type(data):
    result = collection_stub(data)

    assert result.items == ["item1", "item2"]


def test_collection_mastodon_replies_type():
    data = {
        "id": "http://mastodon.example/users/alice/statuses/2343242/replies",
        "type": "Collection",
        "first": {
            "type": "CollectionPage",
            "next": "http://mastodon.example/users/alice/statuses/2343242/replies?only_other_accounts=true&page=true",
            "partOf": "http://mastodon.example/users/alice/statuses/2343242/replies",
            "items": ["http://first.test/item"],
        },
    }
    result = collection_stub(data)

    assert result.items == ["http://first.test/item"]
    assert (
        result.next
        == "http://mastodon.example/users/alice/statuses/2343242/replies?only_other_accounts=true&page=true"
    )
