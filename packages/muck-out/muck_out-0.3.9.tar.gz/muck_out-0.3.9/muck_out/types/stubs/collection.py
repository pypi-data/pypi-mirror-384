from pydantic import Field
from muck_out.validators import IdFieldOrNone, TransformToListOfUris
from .common import CommonAll


class CollectionStub(CommonAll):
    """Abstracts all the ActivityPub collection concepts"""

    items: TransformToListOfUris = Field([], description="""The items""")

    next: IdFieldOrNone = Field(None)
    prev: IdFieldOrNone = Field(None)
    first: IdFieldOrNone = Field(None)
    last: IdFieldOrNone = Field(None)
    total_items: int | None = Field(None, alias="totalItems")
