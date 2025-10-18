from typing import Any
from bovine.activitystreams.utils import id_for_object

from muck_out.transform import transform_to_list_of_uris
from muck_out.types import Collection, CollectionStub


def collection_stub(data: dict[str, Any]) -> CollectionStub:
    """Returns a normalized version of a collection, which possible null values"""
    result = CollectionStub.model_validate(data)

    if not result.items and data.get("orderedItems"):
        result.items = transform_to_list_of_uris(data.get("orderedItems"))

    if isinstance(data.get("first"), dict):
        first = CollectionStub.model_validate(data.get("first"))
        result.next = first.next
        result.items += first.items
        result.first = None

    return result


def convert_items(items: list[dict[str, Any] | str]) -> list[str]:
    """Converts a list of items to a list of ids

    ```pycon
    >>> convert_items([{"id": "https://site.example/1"}, "https://site.example/2"])
    ['https://site.example/1', 'https://site.example/2']

    ```
    """
    return [x for x in (id_for_object(item) for item in items) if x]


def normalize_collection(collection: dict[str, Any]) -> Collection | None:
    """Normalizes a collection"""

    stub = collection_stub(collection)

    if stub.type is None or stub.type not in (
        "Collection",
        "OrderedCollection",
        "CollectionPage",
        "OrderedCollectionPage",
    ):
        return None

    return Collection.model_validate(stub.model_dump())
