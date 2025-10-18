"""
This package contains helper methods allowing one to write nicer
code in a combination of cattle_grid, muck_out, and magic injection.

## Examples

We now illustrate the usage of these methods

### Fetch

The annotations starting with fetch are available whenever, you have
a configured broker and activity exchange. Their usage is as

```python
async def my_method(fetcher: FetchObject):
    obj = await fetcher(
        "http://my.example/actor/id",
        "http://other.example/object/id"
    )
```

We note that the actor id must belong to an actor managed by cattle_grid.

### Parsed

The Parsed- annotations are used in processing, i.e.

```python
@subscribe("some_routing_key")
async def process_actor(actor: ParsedActor):
    ...
```

where one is assumed to process messages of type
[ActivityMessage][cattle_grid.model.ActivityMessage], or something
inheriting from it.

### Transform

```python
@extension.transform(inputs=["parsed"], outputs=[...])
async def transform(
    actor: TransformedActor
) -> dict[str, Any]:
    ...
```

"""

from collections.abc import Awaitable, Callable
from typing import Annotated
from fast_depends import Depends

from muck_out.cattle_grid.transform import (
    transform_activity,
    transform_actor,
    transform_collection,
    transform_embedded_object,
    transform_object,
)
from muck_out.types import Activity, Actor, Object, Collection

from .fetch import (
    fetch_activity_builder,
    fetch_actor_builder,
    fetch_collection_builder,
    fetch_object_builder,
)

from .methods import (
    get_activity,
    get_actor,
    get_collection,
    get_embedded_object,
    get_object,
)


ParsedActivity = Annotated[Activity | None, Depends(get_activity)]
"""Returns the parsed activity from the muck_out extension.

This dependency works for methods that would normally receive
a [ActivityMessage][cattle_grid.model.ActivityMessage], e.g.
the `incoming.*` and `outgoing.*` subscriber of cattle_grid.
"""

ParsedActor = Annotated[Actor | None, Depends(get_actor)]
"""Returns the parsed actor from the muck_out extension.

This dependency works for methods that would normally receive
a [ActivityMessage][cattle_grid.model.ActivityMessage], e.g.
the `incoming.*` and `outgoing.*` subscriber of cattle_grid.
"""

ParsedCollection = Annotated[Collection | None, Depends(get_collection)]
"""Returns the parsed collection from the muck_out extension.

This dependency works for methods that would normally receive
a [ActivityMessage][cattle_grid.model.ActivityMessage], e.g.
the `incoming.*` and `outgoing.*` subscriber of cattle_grid.
"""

ParsedEmbeddedObject = Annotated[Object | None, Depends(get_embedded_object)]
"""Returns the parsed embededed object from an activity from the muck_out extension.

This dependency works for methods that would normally receive
a [ActivityMessage][cattle_grid.model.ActivityMessage], e.g.
the `incoming.*` and `outgoing.*` subscriber of cattle_grid.
"""

ParsedObject = Annotated[Object | None, Depends(get_object)]
"""Returns the parsed object from the muck_out extension.

This dependency works for methods that would normally receive
a [ActivityMessage][cattle_grid.model.ActivityMessage], e.g.
the `incoming.*` and `outgoing.*` subscriber of cattle_grid.
"""

FetchActivity = Annotated[
    Callable[[str, str], Awaitable[Activity | None]], Depends(fetch_activity_builder)
]
"""Returns the activity after fetching it"""
FetchActor = Annotated[
    Callable[[str, str], Awaitable[Actor | None]], Depends(fetch_actor_builder)
]
"""Returns the actor after fetching it"""
FetchCollection = Annotated[
    Callable[[str, str], Awaitable[Collection | None]],
    Depends(fetch_collection_builder),
]
"""Returns the collection after fetching it"""
FetchObject = Annotated[
    Callable[[str, str], Awaitable[Object | None]], Depends(fetch_object_builder)
]
"""Returns the object after fetching it"""

TransformedActivity = Annotated[Activity | None, Depends(transform_activity)]
"""Inside of a running transformer, returns the Activity as transformed by muck_out"""
TransformedActor = Annotated[Actor | None, Depends(transform_actor)]
"""Inside of a running transformer, returns the Actor as transformed by muck_out"""
TransformedCollection = Annotated[Collection | None, Depends(transform_collection)]
"""Inside of a running transformer, returns the Collection as transformed by muck_out"""
TransformedEmbeddedObject = Annotated[Object | None, Depends(transform_embedded_object)]
"""Inside of a running transformer, returns the EmbeddedObject as transformed by muck_out"""
TransformedObject = Annotated[Object | None, Depends(transform_object)]
"""Inside of a running transformer, returns the Object as transformed by muck_out"""
