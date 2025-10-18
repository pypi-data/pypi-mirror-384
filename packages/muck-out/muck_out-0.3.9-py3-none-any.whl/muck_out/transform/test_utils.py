import pytest

from .utils import sanitize_html


@pytest.mark.parametrize(
    "unchanged",
    [
        '<a href="http://actor.test/" class="mention" rel="noopener noreferrer">@actor</a>',
        '<a href="http://actor.test/" class="hashtag" rel="noopener noreferrer">@actor</a>',
        '<a href="http://actor.test/" class="mention hashtag" rel="noopener noreferrer">@actor</a>',
    ],
)
def test_sanitize_html_class_kept(unchanged):
    assert sanitize_html(unchanged) == unchanged


def test_santize_html_class_removed():
    bad = '<a href="http://actor.test/" class="weird" rel="noopener noreferrer">@actor</a>'

    assert (
        sanitize_html(bad)
        == '<a href="http://actor.test/" rel="noopener noreferrer">@actor</a>'
    )
