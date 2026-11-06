### Changes to config

* In Pydantic V2, to specify config on a model, you should set a class attribute called `model_config` to be a dict
  with the key/value pairs you want to be used as the config. The Pydantic V1 behavior to create a class called `Config`
  in the namespace of the parent `BaseModel` subclass is now deprecated.

* When subclassing a model, the `model_config` attribute is inherited. This is helpful in the case where you'd like to use
a base class with a given configuration for many models. Note, if you inherit from multiple `BaseModel` subclasses,
like `class MyModel(Model1, Model2)`, the non-default settings in the `model_config` attribute from the two models
will be merged, and for any settings defined in both, those from `Model2` will override those from `Model1`.

* The following config settings have been removed:
    * `allow_mutation` — this has been removed. You should be able to use [frozen](api/config.md#pydantic.config.ConfigDict) equivalently (inverse of current use).
    * `error_msg_templates`
    * `fields` — this was the source of various bugs, so has been removed.
      You should be able to use `Annotated` on fields to modify them as desired.
    * `getter_dict` — `orm_mode` has been removed, and this implementation detail is no longer necessary.
    * `smart_union`.
    * `underscore_attrs_are_private` — the Pydantic V2 behavior is now the same as if this was always set
      to `True` in Pydantic V1.
    * `json_loads`
    * `json_dumps`
    * `copy_on_model_validation`
    * `post_init_call`

* The following config settings have been renamed:
    * `allow_population_by_field_name` → `populate_by_name`
    * `anystr_lower` → `str_to_lower`
    * `anystr_strip_whitespace` → `str_strip_whitespace`
    * `anystr_upper` → `str_to_upper`
    * `keep_untouched` → `ignored_types`
    * `max_anystr_length` → `str_max_length`
    * `min_anystr_length` → `str_min_length`
    * `orm_mode` → `from_attributes`
    * `schema_extra` → `json_schema_extra`
    * `validate_all` → `validate_default`

See the [`ConfigDict` API reference][pydantic.config.ConfigDict] for more details.
