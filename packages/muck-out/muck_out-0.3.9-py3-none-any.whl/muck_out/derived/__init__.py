from muck_out.derived.object_meta_info import ObjectMetaInfo
from muck_out.derived.util import determine_html_url
from muck_out.types import Actor, Object
from .actor_header_info import ActorHeaderInfo

__all__ = [
    "ActorHeaderInfo",
    "actor_to_header_info",
    "ObjectMetaInfo",
    "object_to_meta_info",
]


def actor_to_header_info(actor: Actor) -> ActorHeaderInfo:
    """Turns an [Actor][muck_out.types.Actor] object into a reduced version
    suitable to display in a header lien for this actor.

    ```python
    >>> from muck_out.testing.examples import actor
    >>> result = actor_to_header_info(actor)
    >>> print(result.model_dump_json(indent=2))
    {
      "id": "http://abel/actor/AFKb0cQunSBv1fC7sWbQYg",
      "avatarUrl": "https://dev.bovine.social/assets/bull-horns.png",
      "name": "The kitty",
      "identifier": "acct:kitty@abel",
      "htmlUrl": "http://abel/@kitty"
    }

    ```
    """
    avatar_url = actor.icon.get("url") if actor.icon else None
    html_url = determine_html_url(actor.url)
    return ActorHeaderInfo(
        id=actor.id,
        name=actor.name,
        identifier=actor.identifiers[0],
        avatar_url=avatar_url,
        html_url=html_url,
    )


def object_to_meta_info(obj: Object) -> ObjectMetaInfo:
    """Turns an object into its meta information


    ```python
    >>> from muck_out.testing.examples import normalized_obj
    >>> result = object_to_meta_info(normalized_obj)
    >>> print(result.model_dump_json(indent=2))
    {
      "id": "https://activitypub.space/post/99",
      "htmlUrl": "https://activitypub.space/post/99",
      "published": "2025-09-06T20:09:12.263000Z",
      "updated": null
    }

    ```
    """
    return ObjectMetaInfo(
        id=obj.id,
        html_url=determine_html_url(obj.url),
        published=obj.published,
        updated=obj.updated,
    )
