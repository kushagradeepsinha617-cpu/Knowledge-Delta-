## Parsing data into a specified type

[`TypeAdapter`][pydantic.type_adapter.TypeAdapter] can be used to apply the parsing logic to populate Pydantic models
in a more ad-hoc way. This function behaves similarly to
[`BaseModel.model_validate`][pydantic.main.BaseModel.model_validate],
but works with arbitrary Pydantic-compatible types.

This is especially useful when you want to parse results into a type that is not a direct subclass of
[`BaseModel`][pydantic.main.BaseModel]. For example:

```python
from typing import List

from pydantic import BaseModel, TypeAdapter


class Item(BaseModel):
    id: int
    name: str


# `item_data` could come from an API call, eg., via something like:
# item_data = requests.get('https://my-api.com/items').json()
item_data = [{'id': 1, 'name': 'My Item'}]

items = TypeAdapter(List[Item]).validate_python(item_data)
print(items)
#> [Item(id=1, name='My Item')]
```

[`TypeAdapter`][pydantic.type_adapter.TypeAdapter] is capable of parsing data into any of the types Pydantic can
handle as fields of a [`BaseModel`][pydantic.main.BaseModel].

!!! info "Performance considerations"
    When creating an instance of [`TypeAdapter`][pydantic.type_adapter.TypeAdapter], the provided type must be analyzed and converted into a pydantic-core
    schema. This comes with some non-trivial overhead, so it is recommended to create a `TypeAdapter` for a given type
    just once and reuse it in loops or other performance-critical code.
