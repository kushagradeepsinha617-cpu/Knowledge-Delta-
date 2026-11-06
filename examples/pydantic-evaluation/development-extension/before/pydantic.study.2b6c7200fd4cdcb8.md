### Url and Dsn types in `pydantic.networks` no longer inherit from `str`

In Pydantic V1 the [`AnyUrl`][pydantic.networks.AnyUrl] type inherited from `str`, and all the other
`Url` and `Dsn` types inherited from these. In Pydantic V2 these types are built on two new `Url` and `MultiHostUrl`
classes using `Annotated`.

Inheriting from `str` had upsides and downsides, and for V2 we decided it would be better to remove this. To use these
types in APIs which expect `str` you'll now need to convert them (with `str(url)`).

Pydantic V2 uses Rust's [Url](https://crates.io/crates/url) crate for URL validation.
Some of the URL validation differs slightly from the previous behavior in V1.
One notable difference is that the new `Url` types append slashes to the validated version if no path is included,
even if a slash is not specified in the argument to a `Url` type constructor. See the example below for this behavior:

```python
from pydantic import AnyUrl

assert str(AnyUrl(url='https://google.com')) == 'https://google.com/'
assert str(AnyUrl(url='https://google.com/')) == 'https://google.com/'
assert str(AnyUrl(url='https://google.com/api')) == 'https://google.com/api'
assert str(AnyUrl(url='https://google.com/api/')) == 'https://google.com/api/'
```

If you still want to use the old behavior without the appended slash, take a look at this [solution](https://github.com/pydantic/pydantic/issues/7186#issuecomment-1690235887).


### Constrained types

The `Constrained*` classes were _removed_, and you should replace them by `Annotated[<type>, Field(...)]`, for example:

```python {test="skip"}
from pydantic import BaseModel, ConstrainedInt


class MyInt(ConstrainedInt):
    ge = 0


class Model(BaseModel):
    x: MyInt
```

...becomes:

```python
from typing_extensions import Annotated

from pydantic import BaseModel, Field

MyInt = Annotated[int, Field(ge=0)]


class Model(BaseModel):
    x: MyInt
```

Read more about it in the [Composing types via `Annotated`](concepts/types.md#composing-types-via-annotated)
docs.

For `ConstrainedStr` you can use [`StringConstraints`][pydantic.types.StringConstraints] instead.

#### Mypy Plugins

Pydantic V2 contains a [mypy](https://mypy.readthedocs.io/en/stable/extending_mypy.html#configuring-mypy-to-use-plugins) plugin in
`pydantic.mypy`.

When using [V1 features](migration.md#continue-using-pydantic-v1-features) the
`pydantic.v1.mypy` plugin might need to also be enabled.

To configure the `mypy` plugins:

=== `mypy.ini`

    ```ini
    [mypy]
    plugins = pydantic.mypy, pydantic.v1.mypy # include `.v1.mypy` if required.
    ```

=== `pyproject.toml`

    ```toml
    [tool.mypy]
    plugins = [
        "pydantic.mypy",
        "pydantic.v1.mypy",
    ]
    ```

## Other changes

* Dropped support for [`email-validator<2.0.0`](https://github.com/JoshData/python-email-validator). Make sure to update
  using `pip install -U email-validator`.
