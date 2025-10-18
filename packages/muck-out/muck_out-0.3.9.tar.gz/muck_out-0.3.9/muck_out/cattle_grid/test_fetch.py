import pytest
from faststream.rabbit import RabbitBroker
from faststream.rabbit.testing import TestRabbitBroker

from cattle_grid.dependencies.globals import global_container

from muck_out.testing.examples import actor

from . import FetchActor


@pytest.fixture
def transform_then_call():
    async def func(method):
        broker = RabbitBroker()

        broker.subscriber("queue")(method)

        @broker.subscriber("fetch", exchange=global_container.exchange)
        async def fetch():
            return {"parsed": {"actor": actor}}

        async with TestRabbitBroker(broker) as br:
            await br.publish({}, "queue")

    return func


async def test_fetch_actor(transform_then_call):
    async def method(fetch: FetchActor):
        result = await fetch("http://actor.test", "http://object.test")
        assert result

    await transform_then_call(method)
