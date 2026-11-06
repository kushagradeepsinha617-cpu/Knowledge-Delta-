## Strict mode with `Field`

For individual fields on a model, you can [set `strict=True` on the field](../api/fields.md#pydantic.fields.Field).
This will cause strict-mode validation to be used for that field, even when the validation methods are called without
`strict=True`.

Only the fields for which `strict=True` is set will be affected:

```python
from pydantic import BaseModel, Field, ValidationError


class User(BaseModel):
    name: str
    age: int
    n_pets: int


user = User(name='John', age='42', n_pets='1')
print(user)
#> name='John' age=42 n_pets=1


class AnotherUser(BaseModel):
    name: str
    age: int = Field(strict=True)
    n_pets: int


try:
    anotheruser = AnotherUser(name='John', age='42', n_pets='1')
except ValidationError as e:
    print(e)
    """
    1 validation error for AnotherUser
    age
      Input should be a valid integer [type=int_type, input_value='42', input_type=str]
    """
```

Note that making fields strict will also affect the validation performed when instantiating the model class:

```python
from pydantic import BaseModel, Field, ValidationError


class Model(BaseModel):
    x: int = Field(strict=True)
    y: int = Field(strict=False)


try:
    Model(x='1', y='2')
except ValidationError as exc:
    print(exc)
    """
    1 validation error for Model
    x
      Input should be a valid integer [type=int_type, input_value='1', input_type=str]
    """
```
