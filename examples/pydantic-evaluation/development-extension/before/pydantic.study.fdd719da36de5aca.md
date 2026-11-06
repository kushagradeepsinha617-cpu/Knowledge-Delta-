### Changes to dataclasses

Pydantic [dataclasses](concepts/dataclasses.md) continue to be useful for enabling the data validation on standard
dataclasses without having to subclass `BaseModel`. Pydantic V2 introduces the following changes to this dataclass behavior:

* When used as fields, dataclasses (Pydantic or vanilla) no longer accept tuples as validation inputs; dicts should be
  used instead.
* The `__post_init__` in Pydantic dataclasses will now be called _after_ validation, rather than before.
    * As a result, the `__post_init_post_parse__` method would have become redundant, so has been removed.
* Pydantic no longer supports `extra='allow'` for Pydantic dataclasses, where extra fields passed to the initializer would be
    stored as extra attributes on the dataclass. `extra='ignore'` is still supported for the purpose of ignoring
    unexpected fields while parsing data, they just won't be stored on the instance.
* Pydantic dataclasses no longer have an attribute `__pydantic_model__`, and no longer use an underlying `BaseModel`
    to perform validation or provide other functionality.
    * To perform validation, generate a JSON schema, or make use of
        any other functionality that may have required `__pydantic_model__` in V1, you should now wrap the dataclass
        with a [`TypeAdapter`][pydantic.type_adapter.TypeAdapter] ([discussed more below](#introduction-of-typeadapter)) and
        make use of its methods.
* In Pydantic V1, if you used a vanilla (i.e., non-Pydantic) dataclass as a field, the config of the parent type would
    be used as though it was the config for the dataclass itself as well. In Pydantic V2, this is no longer the case.
    * In Pydantic V2, to override the config (like you would with `model_config` on a `BaseModel`),
        you can use the `config` parameter on the `@dataclass` decorator.
        See [Dataclass Config](concepts/dataclasses.md#dataclass-config) for examples.
