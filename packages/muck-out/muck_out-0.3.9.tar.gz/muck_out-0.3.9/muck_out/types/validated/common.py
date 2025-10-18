from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from typing import Any


class CommonAll(BaseModel):
    model_config = ConfigDict(
        serialize_by_alias=True,
        validate_by_name=True,
        extra="forbid",
        field_title_generator=lambda field_name, field_info: "",
    )

    field_context: str | list[Any] | None = Field(
        None,
        alias="@context",
        examples=[
            "https://www.w3.org/ns/activitystreams",
            ["https://www.w3.org/ns/activitystreams", {"Hashtag": "as:Hashtag"}],
        ],
    )
    id: str = Field(
        examples=["https://actor.example/some_id"],
        description="id of the activity or object, can be assumed to be globally unique. Some activities such as a Follow request will require an id to be valid. Servers may assume an id to be required. As assigning an id is 'trivial', one should assign one.",
    )


class Common(CommonAll):
    model_config = ConfigDict(serialize_by_alias=True)

    to: list[str] = Field(
        examples=[
            ["https://bob.example"],
            ["https://alice.example", "https://bob.example"],
        ],
        min_length=1,
        description="Array of actors this activity or object is addressed to. It is sane to assume that an activity is addressed to at least one person.",
    )
    cc: list[str] = Field(
        default=[],
        examples=[
            ["https://bob.example"],
            ["https://alice.example", "https://bob.example"],
        ],
        description="Array of actors this activity or object is carbon copied to.",
    )
    published: datetime | None = Field(
        None,
        description="Moment of this activity or object being published",
    )
    type: str = Field(
        examples=["Follow", "Accept", "Create", "Undo", "Like", "Note"],
        description="Type of the activity or activity. Side effects of this activity are determine by this type.",
    )
