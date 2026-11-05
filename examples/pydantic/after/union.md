#### Unions

While union types will still attempt validation of each choice from left to right, they now preserve the type of the
input whenever possible, even if the correct type is not the first choice for which the input would pass validation.
As a demonstration, consider the following example:

```python
from typing import Union

from pydantic import BaseModel


class Model(BaseModel):
    x: Union[int, str]


print(Model(x='1'))
#> x='1'
```

In Pydantic V1, the printed result would have been `x=1`, since the value would pass validation as an `int`.
In Pydantic V2, we recognize that the value is an instance of one of the cases and short-circuit the standard union validation.

To revert to the non-short-circuiting left-to-right behavior of V1, annotate the union with `Field(union_mode='left_to_right')`.
See [Union Mode](./concepts/unions.md#union-modes) for more details.
