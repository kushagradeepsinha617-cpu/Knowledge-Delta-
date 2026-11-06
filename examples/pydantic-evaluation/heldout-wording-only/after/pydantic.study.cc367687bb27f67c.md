

### Partial JSON Parsing

**Starting in v2.7.0**, Pydantic's [JSON parser](https://docs.rs/jiter/latest/jiter/) offers support for partial JSON parsing, which is exposed via [`pydantic_core.from_json`][pydantic_core.from_json]. Here's an example of this feature in action:

```python
from pydantic_core import from_json

partial_json_data = '["aa", "bb", "c'  # (1)!

try:
    result = from_json(partial_json_data, allow_partial=False)
except ValueError as e:
    print(e)  # (2)!
    #> EOF while parsing a string at line 1 column 15

result = from_json(partial_json_data, allow_partial=True)
print(result)  # (3)!
#> ['aa', 'bb']
```

1. The JSON list is incomplete - it's missing a closing `"]`
2. When `allow_partial` is set to `False` (the default), a parsing error occurs.
3. When `allow_partial` is set to `True`, part of the input is deserialized successfully.

This also works for deserializing partial dictionaries. For example:

```python
from pydantic_core import from_json

partial_dog_json = '{"breed": "lab", "name": "fluffy", "friends": ["buddy", "spot", "rufus"], "age'
dog_dict = from_json(partial_dog_json, allow_partial=True)
print(dog_dict)
#> {'breed': 'lab', 'name': 'fluffy', 'friends': ['buddy', 'spot', 'rufus']}
```

!!! tip "Validating LLM Output"
    This feature is particularly beneficial for validating LLM outputs.
    We've written some blog posts about this topic, which you can find [here](https://pydantic.dev/articles).

In future versions of Pydantic, we expect to expand support for this feature through either Pydantic's other JSON validation functions
([`pydantic.main.BaseModel.model_validate_json`][pydantic.main.BaseModel.model_validate_json] and
[`pydantic.type_adapter.TypeAdapter.validate_json`][pydantic.type_adapter.TypeAdapter.validate_json]) or model configuration. Stay tuned 🚀!

For now, you can use [`pydantic_core.from_json`][pydantic_core.from_json] in combination with [`pydantic.main.BaseModel.model_validate`][pydantic.main.BaseModel.model_validate] to achieve the same result. Here's an example:

```python
from pydantic_core import from_json

from pydantic import BaseModel


class Dog(BaseModel):
    breed: str
    name: str
    friends: list


partial_dog_json = '{"breed": "lab", "name": "fluffy", "friends": ["buddy", "spot", "rufus"], "age'
dog = Dog.model_validate(from_json(partial_dog_json, allow_partial=True))
print(repr(dog))
#> Dog(breed='lab', name='fluffy', friends=['buddy', 'spot', 'rufus'])
```

!!! tip
    For partial JSON parsing to work reliably, all fields on the model should have default values.

Check out the following example for a more in-depth look at how to use default values with partial JSON parsing:

!!! example "Using default values with partial JSON parsing"

    ```python
    from typing import Any, Optional, Tuple

    import pydantic_core
    from typing_extensions import Annotated

    from pydantic import BaseModel, ValidationError, WrapValidator


    def default_on_error(v, handler) -> Any:
        """
        Raise a PydanticUseDefault exception if the value is missing.

        This is useful for avoiding errors from partial
        JSON preventing successful validation.
        """
        try:
            return handler(v)
        except ValidationError as exc:
            # there might be other types of errors resulting from partial JSON parsing
            # that you allow here, feel free to customize as needed
            if all(e['type'] == 'missing' for e in exc.errors()):
                raise pydantic_core.PydanticUseDefault()
            else:
                raise


    class NestedModel(BaseModel):
        x: int
        y: str


    class MyModel(BaseModel):
        foo: Optional[str] = None
        bar: Annotated[
            Optional[Tuple[str, int]], WrapValidator(default_on_error)
        ] = None
        nested: Annotated[
            Optional[NestedModel], WrapValidator(default_on_error)
        ] = None


    m = MyModel.model_validate(
        pydantic_core.from_json('{"foo": "x", "bar": ["world",', allow_partial=True)
    )
    print(repr(m))
    #> MyModel(foo='x', bar=None, nested=None)


    m = MyModel.model_validate(
        pydantic_core.from_json(
            '{"foo": "x", "bar": ["world", 1], "nested": {"x":', allow_partial=True
        )
    )
    print(repr(m))
    #> MyModel(foo='x', bar=('world', 1), nested=None)
    ```

