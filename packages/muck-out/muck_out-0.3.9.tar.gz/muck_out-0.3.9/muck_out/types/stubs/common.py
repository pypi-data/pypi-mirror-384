from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, BeforeValidator
from typing import Annotated

from muck_out.validators import TransformToListOfUris
from muck_out.transform.list_utils import list_from_value


class CommonAll(BaseModel):
    """Common base for all ActivityPub objects.

    Note `@context` is normalized to be a list, i.e

    ```pycon
    >>> CommonAll.model_validate({"@context":
    ...     "https://www.w3.org/ns/activitystreams"})
    CommonAll(field_context=['https://www.w3.org/ns/activitystreams'], id=None, type=None)

    ```
    """

    model_config = ConfigDict(serialize_by_alias=True)

    field_context: Annotated[
        list[str | dict] | None, BeforeValidator(list_from_value)
    ] = Field(
        default=["https://www.w3.org/ns/activitystreams"],
        alias="@context",
        examples=[
            ["https://www.w3.org/ns/activitystreams"],
            ["https://www.w3.org/ns/activitystreams", {"Hashtag": "as:Hashtag"}],
        ],
        description="The Json-LD context",
    )
    id: str | None = Field(
        default=None,
        examples=["https://actor.example/some_id"],
        description="id of the activity or object, can be assumed to be globally unique. Some activities such as a Follow request will require an id to be valid. Servers may assume an id to be required. As assigning an id is 'trivial', one should assign one.",
    )
    type: str | None = Field(
        default=None,
        examples=[
            "Follow",
            "Accept",
            "Create",
            "Undo",
            "Like",
            "Note",
            "Actor",
            "Collection",
        ],
        description="Type of the activity or activity. Side effects of this activity are determine by this type.",
    )


class Common(CommonAll):
    to: TransformToListOfUris = Field(
        default=[],
        examples=[
            ["https://bob.example"],
            ["https://alice.example", "https://bob.example"],
        ],
        description="Array of actors this activity or object is addressed to. It is sane to assume that an activity is addressed to at least one person.",
    )
    cc: TransformToListOfUris = Field(
        default=[],
        examples=[
            ["https://bob.example"],
            ["https://alice.example", "https://bob.example"],
        ],
        description="Array of actors this activity or object is carbon copied to.",
    )
    published: datetime | None = Field(
        default=None,
        description="Moment of this activity or object being published",
    )
