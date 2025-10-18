from typing import Any
from muck_out.transform.utils import sanitize_html
from muck_out.types import ObjectStub, Object


def object_stub(data: dict[str, Any]) -> ObjectStub:
    """Constructs a stub from data

    This function is not a direct equivalent to ObjectStub.model_validate
    as functionality happens that is not field to field for

    - `content` filled from `contentMap`

    """
    stub = ObjectStub.model_validate(data)

    if stub.content is None:
        content_map = data.get("contentMap")
        if isinstance(content_map, dict):
            values = content_map.values()
            if len(values) > 0:
                stub.content = sanitize_html(list(content_map.values())[0])

    return stub


def normalize_object(obj: dict[str, Any]) -> Object:
    """Normalizes an object

    :params obj: The object to be normalized
    :returns:
    """

    stub = object_stub(obj)
    result = Object.model_validate(stub.model_dump())

    return result
