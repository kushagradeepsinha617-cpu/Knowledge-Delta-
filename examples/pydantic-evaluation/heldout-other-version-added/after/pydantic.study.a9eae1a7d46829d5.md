## Deprecated fields

The `deprecated` parameter can be used to mark a field as being deprecated. Doing so will result in:

* a runtime deprecation warning emitted when accessing the field.
* `"deprecated": true` being set in the generated JSON schema.

You can set the `deprecated` parameter as one of:

* A string, which will be used as the deprecation message.
* An instance of the `warnings.deprecated` decorator (or the `typing_extensions` backport).
* A boolean, which will be used to mark the field as deprecated with a default `'deprecated'` deprecation message.

### `deprecated` as a string

```python
from typing_extensions import Annotated

from pydantic import BaseModel, Field


class Model(BaseModel):
    deprecated_field: Annotated[int, Field(deprecated='This is deprecated')]


print(Model.model_json_schema()['properties']['deprecated_field'])
#> {'deprecated': True, 'title': 'Deprecated Field', 'type': 'integer'}
```

### `deprecated` via the `warnings.deprecated` decorator

!!! note
    You can only use the `deprecated` decorator in this way if you have
    `typing_extensions` >= 4.9.0 installed.

```python {test="skip"}
import importlib.metadata

from packaging.version import Version
from typing_extensions import Annotated, deprecated

from pydantic import BaseModel, Field

if Version(importlib.metadata.version('typing_extensions')) >= Version('4.9'):

    class Model(BaseModel):
        deprecated_field: Annotated[int, deprecated('This is deprecated')]

        # Or explicitly using `Field`:
        alt_form: Annotated[
            int, Field(deprecated=deprecated('This is deprecated'))
        ]
```

### `deprecated` as a boolean

```python
from typing_extensions import Annotated

from pydantic import BaseModel, Field


class Model(BaseModel):
    deprecated_field: Annotated[int, Field(deprecated=True)]


print(Model.model_json_schema()['properties']['deprecated_field'])
#> {'deprecated': True, 'title': 'Deprecated Field', 'type': 'integer'}
```


!!! note "Support for `category` and `stacklevel`"
    The current implementation of this feature does not take into account the `category` and `stacklevel`
    arguments to the `deprecated` decorator. This might land in a future version of Pydantic.

!!! warning "Accessing a deprecated field in validators"
    When accessing a deprecated field inside a validator, the deprecation warning will be emitted. You can use
    [`catch_warnings`][warnings.catch_warnings] to explicitly ignore it:

    ```python
    import warnings

    from typing_extensions import Self

    from pydantic import BaseModel, Field, model_validator


    class Model(BaseModel):
        deprecated_field: int = Field(deprecated='This is deprecated')

        @model_validator(mode='after')
        def validate_model(self) -> Self:
            with warnings.catch_warnings():
                warnings.simplefilter('ignore', DeprecationWarning)
                self.deprecated_field = self.deprecated_field * 2
    ```
