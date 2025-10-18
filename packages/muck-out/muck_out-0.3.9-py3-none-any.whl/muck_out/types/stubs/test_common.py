import pytest

from .common import Common


@pytest.mark.parametrize(
    "to,expected",
    [
        ("http://remote.test/actor", ["http://remote.test/actor"]),
        ({"id": "http://remote.test/actor"}, ["http://remote.test/actor"]),
    ],
)
def test_common_to(to, expected):
    result = Common(to=to)  # type: ignore

    assert result.to == expected
