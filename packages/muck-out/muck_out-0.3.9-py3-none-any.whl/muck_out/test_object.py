from muck_out.process import normalize_object
from muck_out.types import ObjectStub

from muck_out.testing.examples import sample_object


def test_normalize_object():
    result = normalize_object(sample_object)

    assert result.id == sample_object["id"]
    assert result.context == sample_object["context"]


def test_object_stub():
    result = ObjectStub.model_validate(sample_object)

    assert result.id == sample_object["id"]
    assert result.context == sample_object["context"]
