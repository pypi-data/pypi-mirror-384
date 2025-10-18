from pydantic import Field

from muck_out.validators import HtmlStringOrNone, IdFieldOrNone

from .common import Common


class ActivityStub(Common):
    """
    This represents a first draft of a json-schema that every activities exchanged between servers MUST satisfy and be able to parse. Here 'being able to parse' means making it to the point, where depending on the type, you decide what side effects to perform.

    Generally, the fields actor, to, and cc (and maybe bcc --- not transported) represent how the message is being delivered. The fields actor, type, object, target, content represent how the message is processed by the server.
    """

    actor: IdFieldOrNone = Field(
        default=None,
        examples=["https://actor.example/"],
        description="id of the actor performing this activity. One can assume that the activity is signed by this actor (in some form).",
    )
    object: IdFieldOrNone = Field(
        default=None, description="The object of the activity"
    )
    target: IdFieldOrNone = Field(
        default=None,
        examples=[
            "https://other.example/target_id",
        ],
        description="The target, not sure if needed, included for completeness",
    )
    content: HtmlStringOrNone = Field(
        default=None,
        examples=["🐮", "❤️"],
        description="The content used for example to represent the Emote for a like",
    )
