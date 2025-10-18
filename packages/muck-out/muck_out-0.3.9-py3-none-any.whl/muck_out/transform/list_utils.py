from typing import Any


def list_from_value(value: Any) -> list[Any] | None:
    """Transforms a list into a value

    ```pycon
    >>> list_from_value(["aaa"])
    ['aaa']

    >>> list_from_value("aaa")
    ['aaa']

    >>> list_from_value({"a": 1})
    [{'a': 1}]

    >>> list_from_value([])

    >>> list_from_value(None)

    ```


    :returns: A list or None in case of an empty list or None as argument

    """

    if isinstance(value, list):
        if len(value) == 0:
            return None
        return value
    if isinstance(value, str) or isinstance(value, dict):
        return [value]

    return None


def transform_to_list(item) -> list:
    """Takes an item an turns it into a list"""
    list_of_items = list_from_value(item)
    if list_of_items is None:
        return []

    return list_of_items
