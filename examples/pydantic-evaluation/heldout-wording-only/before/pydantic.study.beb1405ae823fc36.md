## Default values

The `default` parameter is used to define a default value for a field.

```python
from pydantic import BaseModel, Field


class User(BaseModel):
    name: str = Field(default='John Doe')


user = User()
print(user)
#> name='John Doe'
```

!!! note
    If you use the [`Optional`][typing.Optional] annotation, it doesn't mean that the field has a default value of `None`!

You can also use `default_factory` (but not both at the same time) to define a callable that will be called to generate a default value.

```python
from uuid import uuid4

from pydantic import BaseModel, Field


class User(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
```

The default factory can also take a single required argument, in which the case the already validated data will be passed as a dictionary.

```python
from pydantic import BaseModel, EmailStr, Field


class User(BaseModel):
    email: EmailStr
    username: str = Field(default_factory=lambda data: data['email'])


user = User(email='user@example.com')
print(user.username)
#> user@example.com
```

The `data` argument will *only* contain the already validated data, based on the [order of model fields](./models.md#field-ordering)
(the above example would fail if `username` were to be defined before `email`).
