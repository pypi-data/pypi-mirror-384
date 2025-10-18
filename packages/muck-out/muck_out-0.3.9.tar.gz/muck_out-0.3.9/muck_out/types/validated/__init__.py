from pydantic import Field
from typing import Any

from .actor import Actor
from .common import Common
from .object import Object
from .collection import Collection

__all__ = ["Activity", "Actor", "Collection", "Object"]


class Activity(Common):
    """
    This represents a first draft of a json-schema that every activities exchanged between servers MUST satisfy and be able to parse. Here 'being able to parse' means making it to the point, where depending on the type, you decide what side effects to perform.

    Generally, the fields actor, to, and cc (and maybe bcc --- not transported) represent how the message is being delivered. The fields actor, type, object, target, content represent how the message is processed by the server.
    """

    actor: str = Field(
        ...,
        examples=["https://actor.example/"],
        description="""
    id of the actor performing this activity. One can assume that the activity is signed by this actor (in some form).
    """,
    )
    object: str | Object | None = Field(None)
    target: str | dict[str, Any] | None = Field(
        None,
        examples=[
            "https://other.example/target_id",
            {"type": "Note", "content": "meow"},
        ],
        description="""
    The target, not sure if needed, included for completeness
    """,
    )
    content: str | None = Field(
        None,
        examples=["🐮", "❤️"],
        description="The content used for example to represent the Emote for a like",
    )
