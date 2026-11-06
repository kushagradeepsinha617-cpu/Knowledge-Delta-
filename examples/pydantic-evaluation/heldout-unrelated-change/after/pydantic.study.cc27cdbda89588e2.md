### Using `json_schema_extra`

The `json_schema_extra` option can be used to add extra information to the JSON schema, either at the
[Field level](#field-level-customization) or at the [Model level](#model-level-customization).
You can pass a `dict` or a `Callable` to `json_schema_extra`.

#### Using `json_schema_extra` with a `dict`

You can pass a `dict` to `json_schema_extra` to add extra information to the JSON schema:

```python {output="json"}
import json

from pydantic import BaseModel, ConfigDict


class Model(BaseModel):
    a: str

    model_config = ConfigDict(json_schema_extra={'examples': [{'a': 'Foo'}]})


print(json.dumps(Model.model_json_schema(), indent=2))
"""
{
  "examples": [
    {
      "a": "Foo"
    }
  ],
  "properties": {
    "a": {
      "title": "A",
      "type": "string"
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

#### Using `json_schema_extra` with a `Callable`

You can pass a `Callable` to `json_schema_extra` to modify the JSON schema with a function:

```python {output="json"}
import json

from pydantic import BaseModel, Field


def pop_default(s):
    s.pop('default')


class Model(BaseModel):
    a: int = Field(default=1, json_schema_extra=pop_default)


print(json.dumps(Model.model_json_schema(), indent=2))
"""
{
  "properties": {
    "a": {
      "title": "A",
      "type": "integer"
    }
  },
  "title": "Model",
  "type": "object"
}
"""
```

#### Merging `json_schema_extra`

Starting in v2.9, Pydantic merges `json_schema_extra` dictionaries from annotated types.
This pattern offers a more additive approach to merging rather than the previous override behavior.
This can be quite helpful for cases of reusing json schema extra information across multiple types.

We viewed this change largely as a bug fix, as it resolves unintentional differences in the `json_schema_extra` merging behavior
between `BaseModel` and `TypeAdapter` instances - see [this issue](https://github.com/pydantic/pydantic/issues/9210)
for more details.

```python
import json

from typing_extensions import Annotated, TypeAlias

from pydantic import Field, TypeAdapter

ExternalType: TypeAlias = Annotated[
    int, Field(json_schema_extra={'key1': 'value1'})
]

ta = TypeAdapter(
    Annotated[ExternalType, Field(json_schema_extra={'key2': 'value2'})]
)
print(json.dumps(ta.json_schema(), indent=2))
"""
{
  "key1": "value1",
  "key2": "value2",
  "type": "integer"
}
"""
```

!!! note
    We no longer (and never fully did) support composing a mix of `dict` and `callable` type `json_schema_extra` specifications.
    If this is a requirement for your use case, please [open a pydantic issue](https://github.com/pydantic/pydantic/issues/new/choose) and explain your situation - we'd be happy to reconsider this decision when presented with a compelling case.
