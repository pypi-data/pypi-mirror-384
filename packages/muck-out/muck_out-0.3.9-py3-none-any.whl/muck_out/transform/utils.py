import nh3

from copy import deepcopy


allowed_html_tags = {
    "a",
    "abbr",
    "acronym",
    "b",
    "blockquote",
    "code",
    "em",
    "i",
    "li",
    "ol",
    "strong",
    "ul",
    "p",
    "br",
    "span",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "hr",
}
"""The currently allowed list of html tags"""

attributes = deepcopy(nh3.ALLOWED_ATTRIBUTES)

attributes["a"].add("class")


def attribute_filter(tag, attr, value):
    if tag == "a" and attr == "class":
        classes = value.split(" ")
        new_classes = [x for x in classes if x in ["mention", "hashtag"]]
        if len(new_classes) == 0:
            return None
        return " ".join(new_classes)

    return value


def sanitize_html(value: str | None) -> str | None:
    """Cleans html

    ```pycon
    >>> sanitize_html("<p>text</p>")
    '<p>text</p>'

    >>> sanitize_html("<script>alert('xss')</script>")
    ''

    ```
    """
    if isinstance(value, str):
        return nh3.clean(
            value,
            tags=allowed_html_tags,
            attributes=attributes,
            attribute_filter=attribute_filter,
        )
    return None


def remove_html(value: str | None) -> str | None:
    """Removes html

    ```pycon
    >>> remove_html('<a href="http://location.test">location.test</p>')
    'location.test'

    ```
    """

    if isinstance(value, str):
        return nh3.clean(value, tags=set())
    return None
