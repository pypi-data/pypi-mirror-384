import pytest

pytest.importorskip("cattle_grid")

from unittest.mock import MagicMock

from muck_out.testing.examples import actor_example

from .extension import muck_out


async def test_muck_out():
    result = await muck_out(
        {"raw": actor_example}, actor=MagicMock(actor_id="http://actor.test/")
    )

    assert "parsed" in result


async def test_muck_out_mastodon_like():
    like = {
        "@context": "https://www.w3.org/ns/activitystreams",
        "id": "https://mastodon.social/users/the_milkman#likes/251507741",
        "type": "Like",
        "actor": "https://mastodon.social/users/the_milkman",
        "object": "https://dev.bovine.social/html_display/object/01999580-e682-799a-8a43-ae9f5742d148",
    }

    result = await muck_out(
        {"raw": like}, actor=MagicMock(actor_id="http://actor.test/")
    )

    parsed = result.get("parsed", {})

    assert parsed.get("activity")
