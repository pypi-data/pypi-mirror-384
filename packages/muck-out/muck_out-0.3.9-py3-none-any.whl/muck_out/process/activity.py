"""Routines to normalize an ActivityPub activity or object.

The routines here take a dictionary and turn them into another
one."""

import logging

from muck_out.types import Activity, ActivityStub
from .object import normalize_object


logger = logging.getLogger(__name__)


def activity_stub(data: dict, actor_id: str | None = None) -> ActivityStub:
    """Builds the activity stub"""
    stub = ActivityStub.model_validate(data)

    if stub.to == [] and actor_id:
        stub.to = [actor_id]

    return stub


def normalize_activity(activity: dict, actor_id: str | None = None) -> Activity:
    """
    Normalizes activities.

    :param activity: The activity being normalized
    :param actor_id: Actor receiving this activity
    :returns:
    """
    try:
        obj = activity.get("object")
        if isinstance(obj, dict):
            try:
                obj = normalize_object(obj)
            except Exception:
                if isinstance(obj, dict):
                    obj = obj.get("id")

        stub = activity_stub(activity, actor_id=actor_id)
        dumped = stub.model_dump()
        dumped["object"] = obj

        return Activity.model_validate(dumped)

    except Exception as e:
        raise e
