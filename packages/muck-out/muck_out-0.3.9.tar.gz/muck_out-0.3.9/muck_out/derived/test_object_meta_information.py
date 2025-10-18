from datetime import datetime

from pydantic_core import TzInfo
from muck_out.process import normalize_object
from muck_out.testing.examples import sample_object

from . import object_to_meta_info


def test_object_meta_info():
    obj = normalize_object(sample_object)

    meta = object_to_meta_info(obj)

    assert meta.id == sample_object["id"]
    assert meta.html_url == "https://activitypub.space/post/99"
    assert meta.published == datetime(2025, 9, 6, 20, 9, 12, 263000, tzinfo=TzInfo(0))
