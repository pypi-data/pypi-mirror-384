from pydantic import Field
from .common import CommonAll


class Collection(CommonAll):
    """Abstracts all the ActivityPub collection concepts"""

    type: str = Field(
        examples=[
            "Collection",
            "OrderedCollection",
            "CollectionPage",
            "OrdererCollectionPage",
        ],
        description="""Type of object""",
    )

    items: list[str] | None = Field(None, description="""The items""")

    next: str | None = Field(None)
    prev: str | None = Field(None)
    first: str | None = Field(None)
    last: str | None = Field(None)
    total_items: int | None = Field(None, alias="totalItems")
