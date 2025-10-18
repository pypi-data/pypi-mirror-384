import logging
from typing import Any
from urllib.parse import urlparse

from muck_out.transform.utils import remove_html
from muck_out.types import ActorStub, Actor
from muck_out.types.validated.actor import PropertyValue

logger = logging.getLogger(__name__)


def calculate_identifiers(stub: ActorStub) -> list[str]:
    if not stub.id:
        return []
    try:
        domain = urlparse(stub.id).netloc

        if stub.preferred_username:
            return [f"acct:{stub.preferred_username}@{domain}", stub.id]

        return [stub.id]
    except Exception:
        return []


def actor_stub(data: dict[str, Any]) -> ActorStub:
    """Returns the stub actor"""
    stub = ActorStub.model_validate(data)

    if data.get("identifiers") is None:
        stub.identifiers = calculate_identifiers(stub)

    return stub


def normalize_property_value(data: dict[str, Any]) -> PropertyValue | dict[str, Any]:
    if data.get("type") == "PropertyValue":
        return PropertyValue.model_validate(
            {
                "name": remove_html(data.get("name")),
                "value": remove_html(data.get("value")),
            }
        )
    return data


def normalize_actor(data: dict[str, Any]) -> Actor | None:
    """Normalizes an ActivityPub actor"""

    try:
        stub = actor_stub(data)

        if stub.inbox is None:
            return None

        if stub.identifiers is None or len(stub.identifiers) == 0:
            if stub.id is None:
                return
            stub.identifiers = [stub.id]

        return Actor.model_validate(stub.model_dump(by_alias=True))

    except Exception as e:
        logger.info(e)
        return None
