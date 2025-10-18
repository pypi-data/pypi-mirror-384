from pathlib import Path
import click
import json
from pydantic import BaseModel

from .types import Actor, Activity, Object, Collection
from .derived import ActorHeaderInfo, ObjectMetaInfo


@click.group
def main(): ...


def to_json_schema(model: BaseModel, filename: str):
    schema = model.model_json_schema()

    with open(filename, "w") as f:
        json.dump(schema, f, indent=2)


@main.command()
@click.option("--path", default="docs/schemas/")
def schemas(path: str):
    Path(path).mkdir(exist_ok=True, parents=True)
    for obj, name in [
        (Actor, "actor"),
        (Activity, "activity"),
        (Object, "object"),
        (Collection, "collection"),
        (ActorHeaderInfo, "actor-header-info"),
        (ObjectMetaInfo, "object-meta-info"),
    ]:
        to_json_schema(obj, f"{path}/{name}.json")  # type: ignore


if __name__ == "__main__":
    main()
