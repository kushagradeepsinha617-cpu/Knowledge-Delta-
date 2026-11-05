#### Required, optional, and nullable fields

Pydantic V2 changes some of the logic for specifying whether a field annotated as `Optional` is required
(i.e., has no default value) or not (i.e., has a default value of `None` or any other value of the corresponding type), and now more closely matches the
behavior of `dataclasses`. Similarly, fields annotated as `Any` no longer have a default value of `None`.

The following table describes the behavior of field annotations in V2:

| State                                                 | Field Definition            |
|-------------------------------------------------------|-----------------------------|
| Required, cannot be `None`                            | `f1: str`                   |
| Not required, cannot be `None`, is `'abc'` by default | `f2: str = 'abc'`           |
| Required, can be `None`                               | `f3: Optional[str]`         |
| Not required, can be `None`, is `None` by default     | `f4: Optional[str] = None`  |
| Not required, can be `None`, is `'abc'` by default    | `f5: Optional[str] = 'abc'` |
| Required, can be any type (including `None`)          | `f6: Any`                   |
| Not required, can be any type (including `None`)      | `f7: Any = None`            |


!!! note
    A field annotated as `typing.Optional[T]` will be required, and will allow for a value of `None`.
    It does not mean that the field has a default value of `None`. _(This is a breaking change from V1.)_

!!! note
    Any default value if provided makes a field not required.

Here is a code example demonstrating the above:
```python
from typing import Optional

from pydantic import BaseModel, ValidationError


class Foo(BaseModel):
    f1: str  # required, cannot be None
    f2: Optional[str]  # required, can be None - same as str | None
    f3: Optional[str] = None  # not required, can be None
    f4: str = 'Foobar'  # not required, but cannot be None


try:
    Foo(f1=None, f2=None, f4='b')
except ValidationError as e:
    print(e)
    """
    1 validation error for Foo
    f1
      Input should be a valid string [type=string_type, input_value=None, input_type=NoneType]
    """
```
