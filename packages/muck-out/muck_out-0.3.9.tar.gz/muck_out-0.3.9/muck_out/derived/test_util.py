import pytest
from .util import determine_html_url


def test_determine_html_url():
    assert determine_html_url([]) is None


@pytest.mark.parametrize(
    "urls,expected",
    [
        (
            [
                {"mediaType": "unknown", "href": "http://wrong.test"},
                {"mediaType": "text/html", "href": "http://right.test"},
            ],
            "http://right.test",
        ),
        ([{"href": "http://right.test"}], "http://right.test"),
    ],
)
def test_determine_html_url_result(urls, expected):
    assert determine_html_url(urls) == expected
