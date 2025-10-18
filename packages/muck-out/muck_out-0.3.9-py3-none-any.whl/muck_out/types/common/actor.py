from pydantic import BaseModel, ConfigDict, Field

from muck_out.validators import HtmlStringOrNone, IdFieldOrNone, UrlList


class CommonActor(BaseModel):
    model_config = ConfigDict(
        serialize_by_alias=True,
        validate_by_name=True,
        field_title_generator=lambda field_name, field_info: "",
    )
    inbox: IdFieldOrNone = Field(
        default=None,
        examples=["https://actor.example/inbox"],
        description="The inbox of the actor",
    )

    outbox: IdFieldOrNone = Field(
        default=None,
        examples=["https://actor.example/outbox"],
        description="The outbox of the actor",
    )

    followers: IdFieldOrNone = Field(
        default=None,
        examples=["https://actor.example/followers"],
        description="The followers collection of the actor",
    )

    following: IdFieldOrNone = Field(
        default=None,
        examples=["https://actor.example/following"],
        description="The following collection of the actor",
    )

    summary: HtmlStringOrNone = Field(
        default=None,
        examples=["My Fediverse account"],
        description="Description of the actor",
    )

    name: HtmlStringOrNone = Field(
        default=None,
        examples=["Alice"],
        description="Display name of the actor",
    )

    url: UrlList = Field(
        default=[],
        description="A list of urls that expand on the content of the object",
    )
