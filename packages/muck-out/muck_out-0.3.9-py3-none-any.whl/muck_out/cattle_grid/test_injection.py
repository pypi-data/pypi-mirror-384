from typing import Any
import pytest

pytest.importorskip("cattle_grid")

from faststream.rabbit import RabbitBroker
from faststream.rabbit.testing import TestRabbitBroker

from cattle_grid.extensions.load import build_transformer
from cattle_grid.model import ActivityMessage
from cattle_grid.testing.fixtures import *  # type: ignore # noqa

from muck_out.extension import extension
from muck_out.types import Activity, Object

from . import ParsedActivity, ParsedActor, ParsedEmbeddedObject


@pytest.fixture
def transform_then_call(actor_for_test):
    async def func(data: dict[str, Any], method):
        transformer = build_transformer([extension])
        transformed = await transformer({"raw": data}, actor_id=actor_for_test.actor_id)  # type: ignore

        broker = RabbitBroker()
        broker.subscriber("queue")(method)

        print(transformed.get("parsed"))

        message = ActivityMessage(actor=actor_for_test.actor_id, data=transformed)
        async with TestRabbitBroker(broker) as br:
            await br.publish(message.model_dump(mode="json"), "queue")

    return func


async def test_injection_activity(transform_then_call):
    data = {
        "@context": "https://www.w3.org/ns/activitystreams",
        "type": "AnimalSound",
        "actor": "http://abel/actor/AFKb0cQunSBv1fC7sWbQYg",
        "to": ["https://www.w3.org/ns/activitystreams#Public"],
        "cc": ["http://abel/followers/RKsezXFc1SGvQKvucioJxg"],
        "published": "2025-09-17T18:34:00Z",
        "content": "meow",
        "id": "http://abel/simple_storage/019958f4-75e2-7039-b3fe-3538d3230d4f",
    }

    def method(activity: ParsedActivity):
        assert isinstance(activity, Activity)
        assert activity.type == "AnimalSound"
        assert activity.content == "meow"

    await transform_then_call(data, method)


async def test_injection_actor_none(transform_then_call):
    data = {
        "@context": "https://www.w3.org/ns/activitystreams",
        "type": "AnimalSound",
        "actor": "http://abel/actor/AFKb0cQunSBv1fC7sWbQYg",
        "to": ["https://www.w3.org/ns/activitystreams#Public"],
        "cc": ["http://abel/followers/RKsezXFc1SGvQKvucioJxg"],
        "published": "2025-09-17T18:34:00Z",
        "content": "meow",
        "id": "http://abel/simple_storage/019958f4-75e2-7039-b3fe-3538d3230d4f",
    }

    def method(actor: ParsedActor):
        assert actor is None

    await transform_then_call(data, method)


async def test_injection_embedded_object(transform_then_call):
    activity = {
        "@context": [
            "https://www.w3.org/ns/activitystreams",
            {"Hashtag": "as:Hashtag", "sensitive": "as:sensitive"},
        ],
        "actor": "http://actor.example",
        "id": "http://actor.example/activity/JTnMd8Pfuuk",
        "object": {
            "attributedTo": "http://actor.example",
            "content": "text",
            "id": "http://actor.example/object/EsHd36ue8zo",
            "published": "2025-09-09T09:32:38Z",
            "to": [
                "https://www.w3.org/ns/activitystreams#Public",
                "http://remote.example/",
            ],
            "type": "Note",
            "url": [
                "http://remote.example/objects/123",
                "http://other.example/objects/123",
            ],
        },
        "published": "2025-09-09T09:32:38Z",
        "to": [
            "https://www.w3.org/ns/activitystreams#Public",
            "http://remote.example/",
        ],
        "type": "Create",
    }

    def method(activity: ParsedActivity, embedded: ParsedEmbeddedObject):
        assert isinstance(activity, Activity)
        assert isinstance(embedded, Object)

    await transform_then_call(activity, method)
