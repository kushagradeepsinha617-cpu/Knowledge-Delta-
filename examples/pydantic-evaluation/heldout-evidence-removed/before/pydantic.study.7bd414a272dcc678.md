[](){#field-wrap-validator}

- __*Wrap* validators__: are the most flexible of all. You can run code before or after Pydantic and other validators
  process the input, or you can terminate validation immediately, either by returning the value early or by raising an
  error.

    Such validators must be defined with a **mandatory** extra `handler` parameter: a callable taking the value to be validated
    as an argument. Internally, this handler will delegate validation of the value to Pydantic. You are free to wrap the call
    to the handler in a [`try..except`][handling exceptions] block, or not call it at all.

    [handling exceptions]: https://docs.python.org/3/tutorial/errors.html#handling-exceptions

    === "Annotated pattern"

        ```python {lint="skip"}
        from typing import Any

        from typing_extensions import Annotated

        from pydantic import BaseModel, Field, ValidationError, ValidatorFunctionWrapHandler, WrapValidator


        def truncate(value: Any, handler: ValidatorFunctionWrapHandler) -> str:
            try:
                return handler(value)
            except ValidationError as err:
                if err.errors()[0]['type'] == 'string_too_long':
                    return handler(value[:5])
                else:
                    raise


        class Model(BaseModel):
            my_string: Annotated[str, Field(max_length=5), WrapValidator(truncate)]


        print(Model(my_string='abcde'))
        #> my_string='abcde'
        print(Model(my_string='abcdef'))
        #> my_string='abcde'
        ```

    === "Decorator"

        ```python {lint="skip"}
        from typing import Any

        from typing_extensions import Annotated

        from pydantic import BaseModel, Field, ValidationError, ValidatorFunctionWrapHandler, field_validator


        class Model(BaseModel):
            my_string: Annotated[str, Field(max_length=5)]

            @field_validator('my_string', mode='wrap')
            @classmethod
            def truncate(cls, value: Any, handler: ValidatorFunctionWrapHandler) -> str:
                try:
                    return handler(value)
                except ValidationError as err:
                    if err.errors()[0]['type'] == 'string_too_long':
                        return handler(value[:5])
                    else:
                        raise


        print(Model(my_string='abcde'))
        #> my_string='abcde'
        print(Model(my_string='abcdef'))
        #> my_string='abcde'
        ```

!!! note "Validation of default values"
    As mentioned in the [fields documentation](./fields.md#validate-default-values), default values of fields
    are *not* validated unless configured to do so, and thus custom validators will not be applied as well.
