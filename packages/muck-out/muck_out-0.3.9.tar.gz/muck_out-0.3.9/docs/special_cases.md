# Special cases

Here, we document activities that have caused special behavior to be implemented.
We note that code blocks involving `>>>` are run as doctests.

## Mastodon

### Mastodon like

Mastodon sends like activities without recipients, i.e. no `to` property.
This leads would lead to the following behavior

```python
>>> from muck_out.process import normalize_activity
>>> mastodon_like = {
...     "@context": "https://www.w3.org/ns/activitystreams",
...     "id": "https://mastodon.social/users/the_milkman#likes/251507741",
...     "type": "Like",
...     "actor": "https://mastodon.social/users/the_milkman",
...     "object": "https://dev.bovine.social/html_display/object/019"
... }
>>> normalize_activity(mastodon_like)
Traceback (most recent call last):
...
pydantic_core._pydantic_core.ValidationError: 1 validation error for Activity
to
  List should have at least 1 item after validation, not 0 [type=too_short, input_value=[], input_type=list]
    For further information visit https://errors.pydantic.dev/2.11/v/too_short
```

In order to work around this, the actor id processing the activity can be passed:

```python
>>> from muck_out.process import normalize_activity
>>> mastodon_like = {
...     "@context": "https://www.w3.org/ns/activitystreams",
...     "id": "https://mastodon.social/users/the_milkman#likes/251507741",
...     "type": "Like",
...     "actor": "https://mastodon.social/users/the_milkman",
...     "object": "https://dev.bovine.social/html_display/object/019"
... }
>>> result = normalize_activity(mastodon_like,
...      actor_id="https://dev.bovine.social/actor/ABC")
>>> print(result.model_dump_json(indent=2, exclude_none=True))
{
  "@context": [
    "https://www.w3.org/ns/activitystreams"
  ],
  "id": "https://mastodon.social/users/the_milkman#likes/251507741",
  "to": [
    "https://dev.bovine.social/actor/ABC"
  ],
  "cc": [],
  "type": "Like",
  "actor": "https://mastodon.social/users/the_milkman",
  "object": "https://dev.bovine.social/html_display/object/019"
}

```

## Hubzilla

### Hubzilla Add

??? info "the activity"
    ```json
    --8<-- "docs/assets/hubzilla_add.json"
    ```

```python
>>> import json
>>> with open("docs/assets/hubzilla_add.json") as fp:
...     hubzilla_add = json.load(fp)
>>> result = normalize_activity(hubzilla_add,
...      actor_id="https://dev.bovine.social/actor/ABC")
>>> result.field_context = []
>>> print(result.model_dump_json(indent=2, exclude_none=True))
{
  "@context": [],
  "id": "https://zotum.net/activity/72598b50-025c-46fc-ba62-3896a86b7fd0",
  "to": [
    "https://dev.bovine.social/actor/ABC"
  ],
  "cc": [],
  "published": "2025-10-02T08:49:49Z",
  "type": "Add",
  "actor": "https://zotum.net/channel/fentiger",
  "object": "https://macaw.social/users/andypiper#likes/464620",
  "target": "https://zotum.net/conversation/0c47b0fa-4495-4c22-8a1b-508e32300ee9"
}

```