from .actor import ActorStub


def test_identifiers():
    stub = ActorStub.model_validate({"identifiers": "actt:some@domain"})

    assert stub.identifiers == ["actt:some@domain"]
