#### Validator behavior changes

Pydantic V2 includes some changes to type coercion. For example:

* coercing `int`, `float`, and `Decimal` values to strings is now optional and disabled by default, see
  [Coerce Numbers to Strings][pydantic.config.ConfigDict.coerce_numbers_to_str].
* iterable of pairs is no longer coerced to a dict.

See the [Conversion table](concepts/conversion_table.md) for details on Pydantic V2 type coercion defaults.
