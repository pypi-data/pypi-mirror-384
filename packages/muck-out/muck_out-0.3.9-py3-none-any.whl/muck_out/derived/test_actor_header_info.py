from muck_out.testing.examples import actor_example, mitra_actor
from muck_out.process import normalize_actor

from . import actor_to_header_info, ActorHeaderInfo


def test_actor_to_header_info():
    actor = normalize_actor(actor_example)
    assert actor

    info = actor_to_header_info(actor)

    assert info.id == actor_example["id"]
    assert info.identifier == "acct:kitty@abel"
    assert info.name == actor_example["name"]
    assert info.avatar_url == "https://dev.bovine.social/assets/bull-horns.png"


def test_actor_to_header_info_html_url():
    actor = normalize_actor(mitra_actor)
    assert actor

    info = actor_to_header_info(actor)
    assert info.html_url == "http://mitra/users/admin"


def test_actor_to_header_info_serialize_and_deserialize():
    actor = normalize_actor(actor_example)
    assert actor

    info = actor_to_header_info(actor)

    dumped = info.model_dump()

    ActorHeaderInfo.model_validate(dumped)
