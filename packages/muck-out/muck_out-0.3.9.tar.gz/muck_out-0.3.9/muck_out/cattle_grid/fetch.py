from collections.abc import Awaitable, Callable
import json
from faststream.rabbit import RabbitBroker, RabbitExchange
from faststream import Context

from cattle_grid.dependencies import ActivityExchange
from cattle_grid.model import FetchMessage

from muck_out.cattle_grid.methods import data_to_type
from muck_out.types import Activity, Actor, Object, Collection


def fetch_method_for_key_and_type(
    broker: RabbitBroker, exchange: RabbitExchange, key: str, object_type
):
    async def fetch(actor_id: str, object_id: str):
        result = await broker.request(
            FetchMessage(actor=actor_id, uri=object_id),
            routing_key="fetch",
            exchange=exchange,
        )

        result = json.loads(result.body)

        return data_to_type(
            result,
            key,
            object_type,
        )

    return fetch


def fetch_activity_builder(
    exchange: ActivityExchange, broker: RabbitBroker = Context()
) -> Callable[[str, str], Awaitable[Actor | None]]:
    return fetch_method_for_key_and_type(broker, exchange, "activity", Activity)


def fetch_actor_builder(
    exchange: ActivityExchange, broker: RabbitBroker = Context()
) -> Callable[[str, str], Awaitable[Actor | None]]:
    return fetch_method_for_key_and_type(broker, exchange, "actor", Actor)


def fetch_collection_builder(
    exchange: ActivityExchange, broker: RabbitBroker = Context()
) -> Callable[[str, str], Awaitable[Actor | None]]:
    return fetch_method_for_key_and_type(broker, exchange, "collection", Collection)


def fetch_object_builder(
    exchange: ActivityExchange, broker: RabbitBroker = Context()
) -> Callable[[str, str], Awaitable[Actor | None]]:
    return fetch_method_for_key_and_type(broker, exchange, "object", Object)
