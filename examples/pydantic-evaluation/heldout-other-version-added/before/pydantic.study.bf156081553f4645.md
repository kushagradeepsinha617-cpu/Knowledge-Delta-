### Validation context

You can pass a context object to the [validation methods](./models.md#validating-data), which can be accessed
inside the validator functions using the [`context`][pydantic.ValidationInfo.context] property:

```python
from pydantic import BaseModel, ValidationInfo, field_validator


class Model(BaseModel):
    text: str

    @field_validator('text', mode='after')
    @classmethod
    def remove_stopwords(cls, v: str, info: ValidationInfo) -> str:
        if isinstance(info.context, dict):
            stopwords = info.context.get('stopwords', set())
            v = ' '.join(w for w in v.split() if w.lower() not in stopwords)
        return v


data = {'text': 'This is an example document'}
print(Model.model_validate(data))  # no context
#> text='This is an example document'
print(Model.model_validate(data, context={'stopwords': ['this', 'is', 'an']}))
#> text='example document'
```

Similarly, you can [use a context for serialization](../concepts/serialization.md#serialization-context).

??? note "Providing context when directly instantiating a model"
    It is currently not possible to provide a context when directly instantiating a model
    (i.e. when calling `Model(...)`). You can work around this through the use of a
    [`ContextVar`][contextvars.ContextVar] and a custom `__init__` method:

    ```python
    from __future__ import annotations

    from contextlib import contextmanager
    from contextvars import ContextVar
    from typing import Any, Generator

    from pydantic import BaseModel, ValidationInfo, field_validator

    _init_context_var = ContextVar('_init_context_var', default=None)


    @contextmanager
    def init_context(value: dict[str, Any]) -> Generator[None]:
        token = _init_context_var.set(value)
        try:
            yield
        finally:
            _init_context_var.reset(token)


    class Model(BaseModel):
        my_number: int

        def __init__(self, /, **data: Any) -> None:
            self.__pydantic_validator__.validate_python(
                data,
                self_instance=self,
                context=_init_context_var.get(),
            )

        @field_validator('my_number')
        @classmethod
        def multiply_with_context(cls, value: int, info: ValidationInfo) -> int:
            if isinstance(info.context, dict):
                multiplier = info.context.get('multiplier', 1)
                value = value * multiplier
            return value


    print(Model(my_number=2))
    #> my_number=2

    with init_context({'multiplier': 3}):
        print(Model(my_number=2))
        #> my_number=6

    print(Model(my_number=2))
    #> my_number=2
    ```
