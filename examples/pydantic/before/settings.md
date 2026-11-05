### `BaseSettings` has moved to `pydantic-settings`

[`BaseSettings`](api/pydantic_settings.md#pydantic_settings.BaseSettings), the base object for Pydantic
[settings management](concepts/pydantic_settings.md), has been moved to a separate package,
[`pydantic-settings`](https://github.com/pydantic/pydantic-settings).

Also, the `parse_env_var` classmethod has been removed. So, you need to
[customise settings sources](concepts/pydantic_settings.md#customise-settings-sources)
to have your own parsing function.
