## Parameter types

Parameter types are inferred from type annotations on the function, or as [`Any`][typing.Any] if not annotated. All types listed in [types](types.md) can be validated, including Pydantic models and [custom types](types.md#custom-types).
As with the rest of Pydantic, types are by default coerced by the decorator before they're passed to the actual function:

```python
from datetime import date

from pydantic import validate_call


@validate_call
def greater_than(d1: date, d2: date, *, include_equal=False) -> date:  # (1)!
    if include_equal:
        return d1 >= d2
    else:
        return d1 > d2


d1 = '2000-01-01'  # (2)!
d2 = date(2001, 1, 1)
greater_than(d1, d2, include_equal=True)
```

1. Because `include_equal` has no type annotation, it will be inferred as [`Any`][typing.Any].
2. Although `d1` is a string, it will be converted to a [`date`][datetime.date] object.

Type coercion like this can be extremely helpful, but also confusing or not desired (see [model data conversion](models.md#data-conversion)). [Strict mode](strict_mode.md)
can be enabled by using a [custom configuration](#custom-configuration).

!!! note "Validating the return value"
    By default, the return value of the function is **not** validated. To do so, the `validate_return` argument
    of the decorator can be set to `True`.
