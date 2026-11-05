### Changes to `pydantic.BaseModel`

Various method names have been changed; all non-deprecated `BaseModel` methods now have names matching either the
format `model_.*` or `__.*pydantic.*__`. Where possible, we have retained the deprecated methods with their old names
to help ease migration, but calling them will emit `DeprecationWarning`s.

| Pydantic V1 | Pydantic V2  |
| ----------- | ------------ |
| `__fields__` | `model_fields` |
| `__private_attributes__` | `__pydantic_private__` |
| `__validators__` | `__pydantic_validator__` |
| `construct()` | `model_construct()` |
| `copy()` | `model_copy()` |
| `dict()` | `model_dump()` |
| `json_schema()` | `model_json_schema()` |
| `json()` | `model_dump_json()` |
| `parse_obj()` | `model_validate()` |
| `update_forward_refs()` | `model_rebuild()` |
