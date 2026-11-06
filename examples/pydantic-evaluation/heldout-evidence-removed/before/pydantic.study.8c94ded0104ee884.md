## Customizing the `$ref`s in JSON Schema

The format of `$ref`s can be altered by calling [`model_json_schema()`][pydantic.main.BaseModel.model_json_schema]
or [`model_dump_json()`][pydantic.main.BaseModel.model_dump_json] with the `ref_template` keyword argument.
The definitions are always stored under the key `$defs`, but a specified prefix can be used for the references.

This is useful if you need to extend or modify the JSON schema default definitions location. For example, with OpenAPI:

```python {output="json"}
import json

from pydantic import BaseModel
from pydantic.type_adapter import TypeAdapter


class Foo(BaseModel):
    a: int


class Model(BaseModel):
    a: Foo


adapter = TypeAdapter(Model)

print(
    json.dumps(
        adapter.json_schema(ref_template='#/components/schemas/{model}'),
        indent=2,
    )
)
"""
{
  "$defs": {
    "Foo": {
      "properties": {
        "a": {
          "title": "A",
          "type": "integer"
        }
      },
      "required": [
        "a"
      ],
      "title": "Foo",
      "type": "object"
    }
  },
  "properties": {
    "a": {
      "$ref": "#/components/schemas/Foo"
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
