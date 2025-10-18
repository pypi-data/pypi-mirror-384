from muck_out.types import Collection

from .collection import normalize_collection


def test_collection_invalid():
    assert normalize_collection({}) is None


def test_collection_mastodon_outbox_type():
    data = {
        "@context": "https://www.w3.org/ns/activitystreams",
        "id": "http://mastodon.example/users/alice/outbox",
        "type": "OrderedCollection",
        "totalItems": 12360,
        "first": "http://mastodon.example/users/alice/outbox?page=true",
        "last": "http://mastodon.example/users/alice/outbox?min_id=0&page=true",
    }

    result = normalize_collection(data)

    assert isinstance(result, Collection)

    assert result.id == data["id"]
    assert result.total_items == data["totalItems"]
    assert result.first == data["first"]
    assert result.last == data["last"]


def test_collection_mastodon_outbox_page_type():
    data = {
        "@context": "https://www.w3.org/ns/activitystreams",
        "id": "http://mastodon.example/users/alice/outbox?page=true",
        "type": "OrderedCollectionPage",
        "next": "http://mastodon.example/users/alice/outbox?max_id=12&page=true",
        "prev": "http://mastodon.example/users/alice/outbox?min_id=17&page=true",
        "orderedItems": ["item1", {"aaa": "bbb"}, {"id": "item2"}],
    }

    result = normalize_collection(data)

    assert isinstance(result, Collection)

    assert result.id == data["id"]
    assert result.next == data["next"]
    assert result.prev == data["prev"]

    assert result.items == ["item1", "item2"]


def test_collection_mastodon_likes_type():
    data = {
        "id": "http://mastodon.example/users/alice/statuses/2343242/likes",
        "type": "Collection",
        "totalItems": 0,
    }

    result = normalize_collection(data)

    assert isinstance(result, Collection)
    assert result.total_items == 0


def test_collection_mastodon_replies_type():
    data = {
        "id": "http://mastodon.example/users/alice/statuses/2343242/replies",
        "type": "Collection",
        "first": {
            "type": "CollectionPage",
            "next": "http://mastodon.example/users/alice/statuses/2343242/replies?only_other_accounts=true&page=true",
            "partOf": "http://mastodon.example/users/alice/statuses/2343242/replies",
            "items": [],
        },
    }

    result = normalize_collection(data)

    assert isinstance(result, Collection)


def test_collection_page():
    data = {
        "id": "http://mastodon.example/users/alice/statuses/2343242/replies?fake=true",
        "type": "CollectionPage",
        "next": "http://mastodon.example/users/alice/statuses/2343242/replies?only_other_accounts=true&page=true",
        "partOf": "http://mastodon.example/users/alice/statuses/2343242/replies",
        "items": ["http://something.example"],
    }

    result = normalize_collection(data)

    assert isinstance(result, Collection)
    assert result.items == data["items"]
