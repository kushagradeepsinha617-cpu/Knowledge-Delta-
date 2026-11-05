* The `__eq__` method has changed for models.
    * Models can only be equal to other `BaseModel` instances.
    * For two model instances to be equal, they must have the same:
        * Type (or, in the case of generic models, non-parametrized generic origin type)
        * Field values
        * Extra values (only relevant when `model_config['extra'] == 'allow'`)
        * Private attribute values; models with different values of private attributes are no longer equal.
        * Models are no longer equal to the dicts containing their data.
        * Non-generic models of different types are never equal.
        * Generic models with different origin types are never equal. We don't require *exact* type equality so that,
            for example, instances of `MyGenericModel[Any]` could be equal to instances of `MyGenericModel[int]`.
