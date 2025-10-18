from cattle_grid.extensions import Extension
from cattle_grid.dependencies.transformer import ActorTransforming

from . import normalize_data

extension = Extension(name="muck out", module=__name__)


@extension.transform(inputs=["raw"], outputs=["parsed"])
async def muck_out(data: dict, actor: ActorTransforming):
    actor_id = actor.actor_id if actor else None
    return {
        "parsed": normalize_data(data["raw"], actor_id=actor_id).model_dump(
            by_alias=True
        )
    }
