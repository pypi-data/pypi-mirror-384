from pydantic import Field

from muck_out.types.common import CommonActor
from muck_out.validators import (
    TransformToListOfUris,
)

from .common import CommonAll


class ActorStub(CommonAll, CommonActor):
    """Describes an ActivityPub actor"""

    icon: dict | None = Field(
        None,
        examples=[{"type": "Image", "url": "https://actor.example/icon.png"}],
        description="The avatar of the actor",
    )

    also_known_as: list[str] | None = Field(
        None,
        examples=[["https://alice.example", "https://alice.example/profile"]],
        alias="alsoKnownAs",
        description="Other uris associated with the actor",
    )

    preferred_username: str | None = Field(
        None, examples=["john"], alias="preferredUsername"
    )

    identifiers: TransformToListOfUris = Field(
        default=[], description="An ordered list of identifiers"
    )

    # attachments: list[dict | PropertyValue] | None = Field(
    #     None, description="""attachments ... currently used for property values"""
    # )
