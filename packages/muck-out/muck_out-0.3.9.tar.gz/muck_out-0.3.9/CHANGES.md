# changes to muck_out

## 0.3.9

- Update to faststream 0.6
- Add missing doctest to ObjectMetaInfo
- Add missing generation of ObjectMetaInfo schema

## 0.3.8

- Repair usage of camelCase vs snake_case
- Add ObjectMetaInfo
- Make Object.cc non nullable and an empty list by default [muck_out#38](https://codeberg.org/bovine/muck_out/issues/38)
- Use [validate_by_name](https://docs.pydantic.dev/latest/concepts/alias/#configdict-settings) to improve ActorHeaderInfo

## 0.3.7

- normalize public addressing to `https://www.w3.org/ns/activitystreams#Public`
- use datetime for published and updated [muck_out#35](https://codeberg.org/bovine/muck_out/issues/35)
- ensure ActorHeaderInfo serializes and deserializes correctly [muck_out#36](https://codeberg.org/bovine/muck_out/issues/36)

## 0.3.6

- Build ts types library [muck_out#33](https://codeberg.org/bovine/muck_out/issues/33)
- Add missing schema generation step to website [muck_out#32](https://codeberg.org/bovine/muck_out/issues/32)
- Add `actor_to_header_info` [muck_out#30](https://codeberg.org/bovine/muck_out/issues/30)

## 0.3.5

- Include JSON in documentation [muck_out#27](https://codeberg.org/bovine/muck_out/issues/27)
- Relax requiremtns for Parsed* methods [muck_out#28](https://codeberg.org/bovine/muck_out/issues/28)

## 0.3.4

- Add hubzilla add example [muck_out#25](https://codeberg.org/bovine/muck_out/issues/25)
- Add following / followers [muck_out#26](https://codeberg.org/bovine/muck_out/issues/26)
- Ensure `ParsedEmbeddedObject` works with transformer result [muck_out#21](https://codeberg.org/bovine/muck_out/issues/21)
- Add support for mastodon like [muck_out#22](https://codeberg.org/bovine/muck_out/issues/22)

## 0.3.3

- Make serialize_by_alias default for normalized objects [muck_out#19](https://codeberg.org/bovine/muck_out/issues/19)

## 0.3.2

- cattle_grid is no longer a main dependency
- Add methods to work within transformers

## 0.3.1

- Add identifiers to actor [muck_out#14](https://codeberg.org/bovine/muck_out/issues/14)
- Add annotations for fetching objects
- Add annotations to receive parsed objects [muck_out#13](https://codeberg.org/bovine/muck_out/issues/13)

## 0.3.0

- Split into stubs and types
- Allow some classes in links [muck_out#11](https://codeberg.org/bovine/muck_out/issues/11)

## 0.2.0

- Add stub objects [muck_out#6](https://codeberg.org/bovine/muck_out/issues/6)
- Remove griffe-fieldz as dependency [muck_out#5](https://codeberg.org/bovine/muck_out/issues/5)

## 0.1.1

- Fix publish credentials

## 0.1.0

- Add release pipeline [muck_out](https://codeberg.org/bovine/muck_out/issues/2)
