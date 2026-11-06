[](){#field-after-validator}

- __*After* validators__: run after Pydantic's internal validation. They are generally more type safe and thus easier to implement.

    === "Annotated pattern"

        Here is an example of a validator performing a validation check, and returning the value unchanged.

        ```python
        from typing_extensions import Annotated

        from pydantic import AfterValidator, BaseModel, ValidationError


        def is_even(value: int) -> int:
            if value % 2 == 1:
                raise ValueError(f'{value} is not an even number')
            return value  # (1)!


        class Model(BaseModel):
            number: Annotated[int, AfterValidator(is_even)]


        try:
            Model(number=1)
        except ValidationError as err:
            print(err)
            """
            1 validation error for Model
            number
              Value error, 1 is not an even number [type=value_error, input_value=1, input_type=int]
            """
        ```

        1. Note that it is important to return the validated value.

    === "Decorator"

        Here is an example of a validator performing a validation check, and returning the value unchanged,
        this time using the [`field_validator()`][pydantic.field_validator] decorator.

        ```python
        from pydantic import BaseModel, ValidationError, field_validator


        class Model(BaseModel):
            number: int

            @field_validator('number', mode='after')  # (1)!
            @classmethod
            def is_even(cls, value: int) -> int:
                if value % 2 == 1:
                    raise ValueError(f'{value} is not an even number')
                return value  # (2)!


        try:
            Model(number=1)
        except ValidationError as err:
            print(err)
            """
            1 validation error for Model
            number
              Value error, 1 is not an even number [type=value_error, input_value=1, input_type=int]
            """
        ```

        1. `'after'` is the default mode for the decorator, and can be omitted.
        2. Note that it is important to return the validated value.

    ??? example "Example mutating the value"
        Here is an example of a validator making changes to the validated value (no exception is raised).

        === "Annotated pattern"

            ```python
            from typing_extensions import Annotated

            from pydantic import AfterValidator, BaseModel


            def double_number(value: int) -> int:
                return value * 2


            class Model(BaseModel):
                number: Annotated[int, AfterValidator(double_number)]


            print(Model(number=2))
            #> number=4
            ```

        === "Decorator"

            ```python
            from pydantic import BaseModel, field_validator


            class Model(BaseModel):
                number: int

                @field_validator('number', mode='after')  # (1)!
                @classmethod
                def double_number(cls, value: int) -> int:
                    return value * 2


            print(Model(number=2))
            #> number=4
            ```

            1. `'after'` is the default mode for the decorator, and can be omitted.
