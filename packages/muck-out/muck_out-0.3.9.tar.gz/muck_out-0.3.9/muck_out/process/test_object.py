import pytest
from . import object_stub


@pytest.mark.parametrize(
    "data", [{"content": "text"}, {"content": ["text"]}, {"contentMap": {"en": "text"}}]
)
def test_processes_content(data):
    result = object_stub(data)
    assert result.content == "text"
