### Mutable default values

A common source of bugs in Python is to use a mutable object as a default value for a function or method argument,
as the same instance ends up being reused in each call.

The [`dataclasses`][dataclasses] module actually raises an error in this case, indicating that you should use
a [default factory](https://docs.python.org/3/library/dataclasses.html#default-factory-functions) instead.

While the same thing can be done in Pydantic, it is not required. In the event that the default value is not hashable,
Pydantic will create a deep copy of the default value when creating each instance of the model:

```python
from typing import Dict, List

from pydantic import BaseModel


class Model(BaseModel):
    item_counts: List[Dict[str, int]] = [{}]


m1 = Model()
m1.item_counts[0]['a'] = 1
print(m1.item_counts)
#> [{'a': 1}]

m2 = Model()
print(m2.item_counts)
#> [{}]
```
