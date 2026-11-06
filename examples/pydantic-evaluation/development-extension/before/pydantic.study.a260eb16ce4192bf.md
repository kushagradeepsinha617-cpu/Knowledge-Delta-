### Changes to `pydantic.generics.GenericModel`

The `pydantic.generics.GenericModel` class is no longer necessary, and has been removed. Instead, you can now
create generic `BaseModel` subclasses by just adding `Generic` as a parent class on a `BaseModel` subclass directly.
This looks like `class MyGenericModel(BaseModel, Generic[T]): ...`.

Mixing of V1 and V2 models is not supported which means that type parameters of such generic `BaseModel` (V2)
cannot be V1 models.

While it may not raise an error, we strongly advise against using _parametrized_ generics in `isinstance` checks.

  * For example, you should not do `isinstance(my_model, MyGenericModel[int])`.
    However, it is fine to do `isinstance(my_model, MyGenericModel)`. (Note that for standard generics, it would raise
    an error to do a subclass check with a parameterized generic.)
  * If you need to perform `isinstance` checks against parametrized generics, you can do this by subclassing the
    parametrized generic class. This looks like `class MyIntModel(MyGenericModel[int]): ...` and
    `isinstance(my_model, MyIntModel)`.

Find more information in the [Generic models](concepts/models.md#generic-models) documentation.
