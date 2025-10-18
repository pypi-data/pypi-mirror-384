from pydantic import BeforeValidator
from typing import Annotated, Any

from bovine.activitystreams.utils import id_for_object
from muck_out.transform.utils import sanitize_html
from muck_out.transform import transform_to_list_of_uris, transform_url


def safe_html(x) -> str | None:
    if x is None:
        return None
    if isinstance(x, list):
        if len(x) == 0:
            return None
        x = x[0]
    return sanitize_html(x)


def safe_id_for_object(x):
    if isinstance(x, list):
        if len(x) == 0:
            return None
        x = x[0]
    return id_for_object(x)


HtmlStringOrNone = Annotated[str | None, BeforeValidator(safe_html)]
"""Used for strings, which may contain html"""

IdFieldOrNone = Annotated[str | None, BeforeValidator(safe_id_for_object)]
"""Used for fields meant to contain an id"""


UrlList = Annotated[list[dict[str, Any]], BeforeValidator(transform_url)]
"""Transforms a list of urls"""

TransformToListOfUris = Annotated[list[str], BeforeValidator(transform_to_list_of_uris)]
"""Transforms a list of recipients, ensuring it is a list of URIs"""
