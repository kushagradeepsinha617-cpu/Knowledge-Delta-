[](){#field-plain-validator}

- __*Plain* validators__: act similarly to *before* validators but they **terminate validation immediately** after returning,
  so no further validators are called and Pydantic does not do any of its internal validation against the field type.

    === "Annotated pattern"

        ```python
        from typing import Any

        from typing_extensions import Annotated

        from pydantic import BaseModel, PlainValidator


        def val_number(value: Any) -> Any:
            if isinstance(value, int):
                return value * 2
            else:
                return value


        class Model(BaseModel):
            number: Annotated[int, PlainValidator(val_number)]


        print(Model(number=4))
        #> number=8
        print(Model(number='invalid'))  # (1)!
        #> number='invalid'
        ```

        1. Although `'invalid'` shouldn't validate against the `int` type, Pydantic accepts the input.

    === "Decorator"

        ```python
        from typing import Any

        from pydantic import BaseModel, field_validator


        class Model(BaseModel):
            number: int

            @field_validator('number', mode='plain')
            @classmethod
            def val_number(cls, value: Any) -> Any:
                if isinstance(value, int):
                    return value * 2
                else:
                    return value


        print(Model(number=4))
        #> number=8
        print(Model(number='invalid'))  # (1)!
        #> number='invalid'
        ```

        1. Although `'invalid'` shouldn't validate against the `int` type, Pydantic accepts the input.
