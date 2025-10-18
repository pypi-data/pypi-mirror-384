from muck_out.types import Activity, Actor, Object, Collection

from .methods import data_to_type


def transform_activity(data: dict) -> None | Activity:
    return data_to_type(data, "activity", Activity)


def transform_actor(data: dict) -> None | Actor:
    return data_to_type(data, "actor", Actor)


def transform_object(data: dict) -> None | Object:
    return data_to_type(data, "object", Object)


def transform_embedded_object(data: dict) -> None | Object:
    return data_to_type(data, "embedded_object", Object)


def transform_collection(data: dict) -> None | Collection:
    return data_to_type(data, "collection", Collection)
