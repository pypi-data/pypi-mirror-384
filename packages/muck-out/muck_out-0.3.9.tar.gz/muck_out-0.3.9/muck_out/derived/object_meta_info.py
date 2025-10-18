from datetime import datetime
from typing import Annotated
from pydantic import BaseModel, ConfigDict, Field


class ObjectMetaInfo(BaseModel):
    """Derived information suitable to be displayed in a header line."""

    model_config = ConfigDict(
        serialize_by_alias=True,
        extra="forbid",
        field_title_generator=lambda field_name, field_info: "",
        validate_by_name=True,
    )

    id: str = Field(
        examples=["https://actor.example/alice/some/id"],
        description="id of the object, can be assumed to be globally unique.",
    )

    html_url: Annotated[
        str | None,
        Field(
            default=None,
            examples=["https://actor.example/@alice/some/ud"],
            description="Location of a html representation of the object",
            alias="htmlUrl",
        ),
    ]

    published: datetime | None = Field(
        default=None,
        description="Moment of this object being published",
    )

    updated: datetime | None = Field(
        default=None,
        description="Moment of this object being updated",
    )
