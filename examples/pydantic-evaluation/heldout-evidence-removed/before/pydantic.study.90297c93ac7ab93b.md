## Rebuilding a `TypeAdapter`'s schema

In v2.10+, [`TypeAdapter`][pydantic.type_adapter.TypeAdapter]'s support deferred schema building and manual rebuilds. This is helpful for the case of:

* Types with forward references
* Types for which core schema builds are expensive

When you initialize a [`TypeAdapter`][pydantic.type_adapter.TypeAdapter] with a type, Pydantic analyzes the type and creates a core schema for it.
This core schema contains the information needed to validate and serialize data for that type.
See the [architecture documentation](../internals/architecture.md) for more information on core schemas.

If you set [`defer_build`][pydantic.config.ConfigDict.defer_build] to `True` when initializing a `TypeAdapter`,
Pydantic will defer building the core schema until the first time it is needed (for validation or serialization).

In order to manually trigger the building of the core schema, you can call the
[`rebuild`][pydantic.type_adapter.TypeAdapter.rebuild] method on the [`TypeAdapter`][pydantic.type_adapter.TypeAdapter] instance:

```python
from pydantic import ConfigDict, TypeAdapter

ta = TypeAdapter('MyInt', config=ConfigDict(defer_build=True))
