from .activity import activity_stub


def test_mastodon_like():
    mastodon_like = {
        "@context": "https://www.w3.org/ns/activitystreams",
        "id": "https://mastodon.social/users/the_milkman#likes/251507741",
        "type": "Like",
        "actor": "https://mastodon.social/users/the_milkman",
        "object": "https://dev.bovine.social/html_display/object/01999580-e682-799a-8a43-ae9f5742d148",
    }

    actor_id = "http://local.test/actor/id"

    result = activity_stub(mastodon_like, actor_id=actor_id)

    assert result.to == [actor_id]
