from uuid6 import uuid7
from bovine.activitystreams.utils import id_for_object

from muck_out.transform.list_utils import list_from_value


def normalize_to(
    value: None | str | list[str], receiving_actor: str | None
) -> list[str]:
    """Normalizes the to value. A normalized activity
    or object should always be addressed to someone.
    If the activity is not addressed to anyone, the receiving
    actor is assumed to be the recipient

    ```pycon
    >>> normalize_to(None, "http://actor.example")
    ['http://actor.example']

    >>> normalize_to("http://to.example", None)
    ['http://to.example']

    >>> normalize_to(["http://alice.example", "http://bob.example"], None)
    ['http://alice.example', 'http://bob.example']

    ```
    """
    if value is None:
        if receiving_actor is None:
            raise ValueError(
                "Cannot set receiving actor as fake recipient if it isn't specified"
            )
        return [receiving_actor]
    return list_from_value(value)  # type:ignore


def normalize_id(activity: dict) -> str:
    """
    Creates a normalized id

    ```pycon
    >>> normalize_id({"id": "http://id.example"})
    'http://id.example'

    >>> normalize_id({})
    Traceback (most recent call last):
        ...
    ValueError: Cannot fake id if actor is not present

    ```
    """
    result = activity.get("id")
    if result is not None:
        return result
    actor_id = id_for_object(activity.get("actor"))

    if actor_id is None:
        raise ValueError("Cannot fake id if actor is not present")

    return f"{actor_id}#fake_id" + str(uuid7())


def normalize_url(url):
    if url is None:
        return
    if isinstance(url, str):
        url = {"type": "Link", "href": url}

    return list_from_value(url)


def normalize_to_id(attributed_to) -> str | None:
    if isinstance(attributed_to, list) and len(attributed_to) == 1:
        attributed_to = attributed_to[0]

    return id_for_object(attributed_to)  # type: ignore
