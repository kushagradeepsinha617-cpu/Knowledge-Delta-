## Type coercions in strict mode

For most types, when validating data from python in strict mode, only the instances of the exact types are accepted.
For example, when validating an `int` field, only instances of `int` are accepted; passing instances of `float` or `str`
will result in raising a `ValidationError`.

Note that we are looser when validating data from JSON in strict mode. For example, when validating a `UUID` field,
instances of `str` will be accepted when validating from JSON, but not from python:

```python
import json
from uuid import UUID

from pydantic import BaseModel, ValidationError


class MyModel(BaseModel):
    guid: UUID


data = {'guid': '12345678-1234-1234-1234-123456789012'}

print(MyModel.model_validate(data))  # OK: lax
#> guid=UUID('12345678-1234-1234-1234-123456789012')

print(
    MyModel.model_validate_json(json.dumps(data), strict=True)
)  # OK: strict, but from json
#> guid=UUID('12345678-1234-1234-1234-123456789012')

try:
    MyModel.model_validate(data, strict=True)  # Not OK: strict, from python
except ValidationError as exc:
    print(exc.errors(include_url=False))
    """
    [
        {
            'type': 'is_instance_of',
            'loc': ('guid',),
            'msg': 'Input should be an instance of UUID',
            'input': '12345678-1234-1234-1234-123456789012',
            'ctx': {'class': 'UUID'},
        }
    ]
    """
```

For more details about what types are allowed as inputs in strict mode, you can review the
[Conversion Table](conversion_table.md).
