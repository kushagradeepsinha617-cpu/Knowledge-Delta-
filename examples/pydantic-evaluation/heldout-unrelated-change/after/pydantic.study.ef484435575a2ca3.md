## Validate default values

By default, Pydantic will *not* validate default values. The `validate_default` field parameter
(or the [`validate_default`][pydantic.ConfigDict.validate_default] configuration value) can be used
to enable this behavior:

```python
from pydantic import BaseModel, Field, ValidationError


class User(BaseModel):
    age: int = Field(default='twelve', validate_default=True)


try:
    user = User()
except ValidationError as e:
    print(e)
    """
    1 validation error for User
    age
      Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='twelve', input_type=str]
    """
```
