[](){#field-before-validator}

- __*Before* validators__: run before Pydantic's internal parsing and validation (e.g. coercion of a `str` to an `int`).
  These are more flexible than [*after* validators](#field-after-validator), but they also have to deal with the raw input, which
  in theory could be any arbitrary object. The value returned from this callable is then validated against the provided type annotation
  by Pydantic.

    === "Annotated pattern"

        ```python
        from typing import Any, List

        from typing_extensions import Annotated

        from pydantic import BaseModel, BeforeValidator, ValidationError


        def ensure_list(value: Any) -> Any:  # (1)!
            if not isinstance(value, list):  # (2)!
                return [value]
            else:
                return value


        class Model(BaseModel):
            numbers: Annotated[List[int], BeforeValidator(ensure_list)]


        print(Model(numbers=2))
        #> numbers=[2]
        try:
            Model(numbers='str')
        except ValidationError as err:
            print(err)  # (3)!
            """
            1 validation error for Model
            numbers.0
              Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='str', input_type=str]
            """
        ```

        1. Notice the use of [`Any`][typing.Any] as a type hint for `value`. *Before* validators take the raw input, which
           can be anything.

        2. Note that you might want to check for other sequence types (such as tuples) that would normally successfully
           validate against the `list` type. *Before* validators give you more flexibility, but you have to account for
           every possible case.

        3. Pydantic still performs validation against the `int` type, no matter if our `ensure_list` validator
           did operations on the original input type.

    === "Decorator"

        ```python
        from typing import Any, List

        from pydantic import BaseModel, ValidationError, field_validator


        class Model(BaseModel):
            numbers: List[int]

            @field_validator('numbers', mode='before')
            @classmethod
            def ensure_list(cls, value: Any) -> Any:  # (1)!
                if not isinstance(value, list):  # (2)!
                    return [value]
                else:
                    return value


        print(Model(numbers=2))
        #> numbers=[2]
        try:
            Model(numbers='str')
        except ValidationError as err:
            print(err)  # (3)!
            """
            1 validation error for Model
            numbers.0
              Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='str', input_type=str]
            """
        ```

        1. Notice the use of [`Any`][typing.Any] as a type hint for `value`. *Before* validators take the raw input, which
           can be anything.

        2. Note that you might want to check for other sequence types (such as tuples) that would normally successfully
           validate against the `list` type. *Before* validators give you more flexibility, but you have to account for
           every possible case.

        3. Pydantic still performs validation against the `int` type, no matter if our `ensure_list` validator
           did operations on the original input type.
