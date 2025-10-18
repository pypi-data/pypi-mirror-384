from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

from muck_out.validators import HtmlStringOrNone, IdFieldOrNone


class CommonObject(BaseModel):
    model_config = ConfigDict(
        serialize_by_alias=True,
        validate_by_name=True,
        field_title_generator=lambda field_name, field_info: "",
    )

    updated: datetime | None = Field(
        default=None,
        description="Moment of this object being updated",
    )
    summary: HtmlStringOrNone = Field(
        default=None,
        description="The summary of the object",
    )
    name: HtmlStringOrNone = Field(
        default=None,
        description="The name of the object",
    )
    in_reply_to: IdFieldOrNone = Field(
        None,
        description="The object being replied to. Currently a string. Not sure if this is what I want.",
        alias="inReplyTo",
    )
    context: IdFieldOrNone = Field(None, description="The context of the object")
