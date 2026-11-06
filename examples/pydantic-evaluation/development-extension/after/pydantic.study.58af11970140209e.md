### Input types are not preserved

In Pydantic V1 we made great efforts to preserve the types of all field inputs for generic collections when they were
proper subtypes of the field annotations. For example, given the annotation `Mapping[str, int]` if you passed in a
`collection.Counter()` you'd get a `collection.Counter()` as the value.

Supporting this behavior in V2 would have negative performance implications for the general case
(we'd have to check types every time) and would add a lot of complexity to validation. Further, even in V1 this behavior
was inconsistent and partially broken: it did not work for many types (`str`, `UUID`, etc.), and for generic
collections it's impossible to re-build the original input correctly without a lot of special casing
(consider `ChainMap`; rebuilding the input is necessary because we need to replace values after validation, e.g.
if coercing strings to ints).

In Pydantic V2 we no longer attempt to preserve the input type in all cases; instead, we only promise that the output
type will match the type annotations.

Going back to the `Mapping` example, we promise the output will be a valid `Mapping`, and in practice it will be a
plain `dict`:

```python
from typing import Mapping

from pydantic import TypeAdapter


class MyDict(dict):
    pass


ta = TypeAdapter(Mapping[str, int])
v = ta.validate_python(MyDict())
print(type(v))
#> <class 'dict'>
```

If you want the output type to be a specific type, consider annotating it as such or implementing a custom validator:

```python
from typing import Any, Mapping, TypeVar

from typing_extensions import Annotated

from pydantic import (
    TypeAdapter,
    ValidationInfo,
    ValidatorFunctionWrapHandler,
    WrapValidator,
)


def restore_input_type(
    value: Any, handler: ValidatorFunctionWrapHandler, _info: ValidationInfo
) -> Any:
    return type(value)(handler(value))


T = TypeVar('T')
PreserveType = Annotated[T, WrapValidator(restore_input_type)]


ta = TypeAdapter(PreserveType[Mapping[str, int]])


class MyDict(dict):
    pass


v = ta.validate_python(MyDict())
assert type(v) is MyDict
```

While we don't promise to preserve input types everywhere, we _do_ preserve them for subclasses of `BaseModel`,
and for dataclasses:

```python
import pydantic.dataclasses
from pydantic import BaseModel


class InnerModel(BaseModel):
    x: int


class OuterModel(BaseModel):
    inner: InnerModel


class SubInnerModel(InnerModel):
    y: int


m = OuterModel(inner=SubInnerModel(x=1, y=2))
print(m)
#> inner=SubInnerModel(x=1, y=2)


@pydantic.dataclasses.dataclass
class InnerDataclass:
    x: int


@pydantic.dataclasses.dataclass
class SubInnerDataclass(InnerDataclass):
    y: int


@pydantic.dataclasses.dataclass
class OuterDataclass:
    inner: InnerDataclass


d = OuterDataclass(inner=SubInnerDataclass(x=1, y=2))
print(d)
#> OuterDataclass(inner=SubInnerDataclass(x=1, y=2))
```
