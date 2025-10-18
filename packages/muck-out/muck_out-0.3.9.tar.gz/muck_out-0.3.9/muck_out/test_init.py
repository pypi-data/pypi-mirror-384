from . import normalize_data as normalize


def test_normalize():
    normalize({})


def test_normalize_activity():
    result = normalize(
        {
            "id": "http://actor.example/2",
            "type": "Create",
            "to": ["http://remote.example"],
            "actor": "http://actor.example/",
            "object": {
                "type": "Note",
                "id": "http://actor.example/1",
                "to": ["http://remote.example"],
                "attributedTo": "http://actor.example/",
                "content": "moo",
            },
        }
    )

    assert result.activity
    assert result.embedded_object
