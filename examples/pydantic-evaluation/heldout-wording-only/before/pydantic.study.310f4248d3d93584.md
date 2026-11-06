### Using an `AliasGenerator`

??? api "API Documentation"

    [`pydantic.aliases.AliasGenerator`][pydantic.aliases.AliasGenerator]<br>


`AliasGenerator` is a class that allows you to specify multiple alias generators for a model.
You can use an `AliasGenerator` to specify different alias generators for validation and serialization.

This is particularly useful if you need to use different naming conventions for loading and saving data,
but you don't want to specify the validation and serialization aliases for each field individually.

For example:

```python
from pydantic import AliasGenerator, BaseModel, ConfigDict


class Tree(BaseModel):
    model_config = ConfigDict(
        alias_generator=AliasGenerator(
            validation_alias=lambda field_name: field_name.upper(),
            serialization_alias=lambda field_name: field_name.title(),
        )
    )

    age: int
    height: float
    kind: str


t = Tree.model_validate({'AGE': 12, 'HEIGHT': 1.2, 'KIND': 'oak'})
print(t.model_dump(by_alias=True))
#> {'Age': 12, 'Height': 1.2, 'Kind': 'oak'}
```
