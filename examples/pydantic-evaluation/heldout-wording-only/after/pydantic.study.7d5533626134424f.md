

## Field aliases

!!! tip
    Read more about aliases in the [dedicated section](./alias.md).

For validation and serialization, you can define an alias for a field.

There are three ways to define an alias:

* `Field(alias='foo')`
* `Field(validation_alias='foo')`
* `Field(serialization_alias='foo')`

The `alias` parameter is used for both validation _and_ serialization. If you want to use
_different_ aliases for validation and serialization respectively, you can use the`validation_alias`
and `serialization_alias` parameters, which will apply only in their respective use cases.

Here is an example of using the `alias` parameter:

```python
from pydantic import BaseModel, Field


class User(BaseModel):
    name: str = Field(alias='username')


user = User(username='johndoe')  # (1)!
print(user)
#> name='johndoe'
print(user.model_dump(by_alias=True))  # (2)!
#> {'username': 'johndoe'}
```

1. The alias `'username'` is used for instance creation and validation.
2. We are using `model_dump` to convert the model into a serializable format.

    You can see more details about [`model_dump`][pydantic.main.BaseModel.model_dump] in the API reference.

    Note that the `by_alias` keyword argument defaults to `False`, and must be specified explicitly to dump
    models using the field (serialization) aliases.

    When `by_alias=True`, the alias `'username'` is also used during serialization.

If you want to use an alias _only_ for validation, you can use the `validation_alias` parameter:

```python
from pydantic import BaseModel, Field


class User(BaseModel):
    name: str = Field(validation_alias='username')


user = User(username='johndoe')  # (1)!
print(user)
#> name='johndoe'
print(user.model_dump(by_alias=True))  # (2)!
#> {'name': 'johndoe'}
```

1. The validation alias `'username'` is used during validation.
2. The field name `'name'` is used during serialization.

If you only want to define an alias for _serialization_, you can use the `serialization_alias` parameter:

```python
from pydantic import BaseModel, Field


class User(BaseModel):
    name: str = Field(serialization_alias='username')


user = User(name='johndoe')  # (1)!
print(user)
#> name='johndoe'
print(user.model_dump(by_alias=True))  # (2)!
#> {'username': 'johndoe'}
```

1. The field name `'name'` is used for validation.
2. The serialization alias `'username'` is used for serialization.

!!! note "Alias precedence and priority"
    In case you use `alias` together with `validation_alias` or `serialization_alias` at the same time,
    the `validation_alias` will have priority over `alias` for validation, and `serialization_alias` will have priority
    over `alias` for serialization.

    If you use an `alias_generator` in the [Model Config][pydantic.config.ConfigDict.alias_generator], you can control
    the order of precedence for specified field vs generated aliases via the `alias_priority` setting. You can read more about alias precedence [here](../concepts/alias.md#alias-precedence).


??? tip "VSCode and Pyright users"
    In VSCode, if you use the [Pylance](https://marketplace.visualstudio.com/items?itemName=ms-python.vscode-pylance)
    extension, you won't see a warning when instantiating a model using a field's alias:

    ```python
    from pydantic import BaseModel, Field


    class User(BaseModel):
        name: str = Field(alias='username')


    user = User(username='johndoe')  # (1)!
    ```

    1. VSCode will NOT show a warning here.

    When the `'alias'` keyword argument is specified, even if you set `populate_by_name` to `True` in the
    [Model Config][pydantic.config.ConfigDict.populate_by_name], VSCode will show a warning when instantiating
    a model using the field name (though it will work at runtime) — in this case, `'name'`:

    ```python
    from pydantic import BaseModel, ConfigDict, Field


    class User(BaseModel):
        model_config = ConfigDict(populate_by_name=True)

        name: str = Field(alias='username')


    user = User(name='johndoe')  # (1)!
    ```

    1. VSCode will show a warning here.

    To "trick" VSCode into preferring the field name, you can use the `str` function to wrap the alias value.
    With this approach, though, a warning is shown when instantiating a model using the alias for the field:

    ```python
    from pydantic import BaseModel, ConfigDict, Field


    class User(BaseModel):
        model_config = ConfigDict(populate_by_name=True)

        name: str = Field(alias=str('username'))  # noqa: UP018


    user = User(name='johndoe')  # (1)!
    user = User(username='johndoe')  # (2)!
    ```

    1. Now VSCode will NOT show a warning
    2. VSCode will show a warning here, though

    This is discussed in more detail in [this issue](https://github.com/pydantic/pydantic/issues/5893).

    ### Validation Alias

    Even though Pydantic treats `alias` and `validation_alias` the same when creating model instances, VSCode will not
    use the `validation_alias` in the class initializer signature. If you want VSCode to use the `validation_alias`
    in the class initializer, you can instead specify both an `alias` and `serialization_alias`, as the
    `serialization_alias` will override the `alias` during serialization:

    ```python
    from pydantic import BaseModel, Field


    class MyModel(BaseModel):
        my_field: int = Field(validation_alias='myValidationAlias')
    ```
    with:
    ```python
    from pydantic import BaseModel, Field


    class MyModel(BaseModel):
        my_field: int = Field(
            ...,
            alias='myValidationAlias',
            serialization_alias='my_serialization_alias',
        )


    m = MyModel(myValidationAlias=1)
    print(m.model_dump(by_alias=True))
    #> {'my_serialization_alias': 1}
    ```

[](){#field-constraints}

