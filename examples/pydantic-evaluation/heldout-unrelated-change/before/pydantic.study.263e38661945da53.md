## The annotated pattern

To apply constraints or attach [`Field()`][pydantic.fields.Field] functions to a model field, Pydantic
supports the [`Annotated`][typing.Annotated] typing construct to attach metadata to an annotation:

```python
from typing_extensions import Annotated

from pydantic import BaseModel, Field, WithJsonSchema


class Model(BaseModel):
    name: Annotated[str, Field(strict=True), WithJsonSchema({'extra': 'data'})]
```

As far as static type checkers are concerned, `name` is still typed as `str`, but Pydantic leverages
the available metadata to add validation logic, type constraints, etc.

Using this pattern has some advantages:

- Using the `f: <type> = Field(...)` form can be confusing and might trick users into thinking `f`
  has a default value, while in reality it is still required.
- You can provide an arbitrary amount of metadata elements for a field. As shown in the example above,
  the [`Field()`][pydantic.fields.Field] function only supports a limited set of constraints/metadata,
  and you may have to use different Pydantic utilities such as [`WithJsonSchema`][pydantic.WithJsonSchema]
  in some cases.
- Types can be made reusable (see the documentation on [custom types](./types.md#using-the-annotated-pattern)
  using this pattern).

However, note that certain arguments to the [`Field()`][pydantic.fields.Field] function (namely, `default`,
`default_factory`, and `alias`) are taken into account by static type checkers to synthesize a correct
`__init__` method. The annotated pattern is *not* understood by them, so you should use the normal
assignment form instead.

!!! tip
    The annotated pattern can also be used to add metadata to specific parts of the type. For instance,
    [validation constraints](#field-constraints) can be added this way:

    ```python
    from typing import List

    from typing_extensions import Annotated

    from pydantic import BaseModel, Field


    class Model(BaseModel):
        int_list: List[Annotated[int, Field(gt=0)]]
        # Valid: [1, 3]
        # Invalid: [-1, 2]
    ```
