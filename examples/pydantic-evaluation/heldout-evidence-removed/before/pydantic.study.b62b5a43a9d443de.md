### `WithJsonSchema` annotation

??? api "API Documentation"
    [`pydantic.json_schema.WithJsonSchema`][pydantic.json_schema.WithJsonSchema]<br>

!!! tip
    Using [`WithJsonSchema`][pydantic.json_schema.WithJsonSchema] is preferred over
    [implementing `__get_pydantic_json_schema__`](#implementing_get_pydantic_json_schema) for custom types,
    as it's more simple and less error-prone.

The [`WithJsonSchema`][pydantic.json_schema.WithJsonSchema] annotation can be used to override the generated (base)
JSON schema for a given type without the need to implement `__get_pydantic_core_schema__`
or `__get_pydantic_json_schema__` on the type itself. Note that this overrides the whole JSON Schema generation process
for the field (in the following example, the `'type'` also needs to be provided).

```python {output="json"}
import json

from typing_extensions import Annotated

from pydantic import BaseModel, WithJsonSchema

MyInt = Annotated[
    int,
    WithJsonSchema({'type': 'integer', 'examples': [1, 0, -1]}),
]


class Model(BaseModel):
    a: MyInt


print(json.dumps(Model.model_json_schema(), indent=2))
"""
{
  "properties": {
    "a": {
      "examples": [
        1,
        0,
        -1
      ],
      "title": "A",
      "type": "integer"
    }
  },
  "required": [
    "a"
  ],
  "title": "Model",
  "type": "object"
}
"""
```

!!! note
    You might be tempted to use the [`WithJsonSchema`][pydantic.json_schema.WithJsonSchema] annotation
    to fine-tune the JSON Schema of fields having [validators](./validators.md) attached. Instead, it
    is recommended to use [the `json_schema_input_type` argument](./validators.md#json-schema-and-field-validators).
