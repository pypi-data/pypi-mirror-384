from .collection import CollectionStub


def test_collection_stub_embedded_first():
    first_id = "http://mastodon.example/users/alice/statuses/2343242/replies?first=true"
    data = {
        "id": "http://mastodon.example/users/alice/statuses/2343242/replies",
        "type": "Collection",
        "first": {
            "id": first_id,
            "type": "CollectionPage",
            "next": "http://mastodon.example/users/alice/statuses/2343242/replies?only_other_accounts=true&page=true",
            "partOf": "http://mastodon.example/users/alice/statuses/2343242/replies",
            "items": [],
        },
    }
    result = CollectionStub.model_validate(data)

    assert result.first == first_id


def test_collection_mastodon_outbox_page_type():
    data = {
        "items": ["item1", {"aaa": "bbb"}, {"id": "item2"}],
    }
    result = CollectionStub.model_validate(data)

    assert result.items == ["item1", "item2"]
