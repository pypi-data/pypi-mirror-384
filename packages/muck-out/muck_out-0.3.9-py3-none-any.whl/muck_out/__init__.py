"""
This package contains tools to turn ActivityPub messages
into something cleaner. Its takes include

- Normalization
- Validation


"""

import logging

from pydantic import BaseModel, Field

from .types import Activity, Object, Actor, Collection

from .process import (
    normalize_activity,
    normalize_object,
    normalize_collection,
    normalize_actor,
)


logger = logging.getLogger(__name__)


class NormalizationResult(BaseModel):
    object: Object | None = Field(default=None)
    activity: Activity | None = Field(default=None)
    embedded_object: Object | None = Field(default=None)
    actor: Actor | None = Field(default=None)
    collection: Collection | None = Field(default=None)


def normalize_data(data: dict, actor_id: str | None = None) -> NormalizationResult:
    """Normalizes the object"""

    def result_or_none(func):
        try:
            return func(data)
        except Exception as e:
            logger.debug(e)

            return None

    try:
        activity = normalize_activity(data, actor_id=actor_id)
    except Exception:
        activity = None

    if activity and isinstance(activity.object, Object):
        embedded_object = activity.object
        activity.object = embedded_object.id
    else:
        embedded_object = None

    return NormalizationResult(
        object=result_or_none(normalize_object),
        activity=activity,
        embedded_object=embedded_object,
        actor=result_or_none(normalize_actor),
        collection=result_or_none(normalize_collection),
    )
