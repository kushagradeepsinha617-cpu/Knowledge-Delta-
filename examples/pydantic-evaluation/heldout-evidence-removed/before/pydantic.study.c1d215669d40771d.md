## Ordering of validators

When using the [annotated pattern](#using-the-annotated-pattern), the order in which validators are applied
is defined as follows: [*before*](#field-before-validator) and [*wrap*](#field-wrap-validator) validators
are run from right to left, and [*after*](#field-after-validator) validators are then run from left to right:

```python {lint="skip" test="skip"}
from pydantic import AfterValidator, BaseModel, BeforeValidator, WrapValidator


class Model(BaseModel):
    name: Annotated[
        str,
        AfterValidator(runs_3rd),
        AfterValidator(runs_4th),
        BeforeValidator(runs_2nd),
        WrapValidator(runs_1st),
    ]
```

Internally, validators defined using [the decorator](#using-the-decorator-pattern) are converted to their annotated
form counterpart and added last after the existing metadata for the field. This means that the same ordering
logic applies.
