### Caching Strings

**Starting in v2.7.0**, Pydantic's [JSON parser](https://docs.rs/jiter/latest/jiter/) offers support for configuring how Python strings are cached during JSON parsing and validation (when Python strings are constructed from Rust strings during Python validation, e.g. after `strip_whitespace=True`).
The `cache_strings` setting is exposed via both [model config][pydantic.config.ConfigDict] and [`pydantic_core.from_json`][pydantic_core.from_json].

The `cache_strings` setting can take any of the following values:

* `True` or `'all'` (the default): cache all strings
* `'keys'`: cache only dictionary keys, this **only** applies when used with [`pydantic_core.from_json`][pydantic_core.from_json] or when parsing JSON using [`Json`][pydantic.types.Json]
* `False` or `'none'`: no caching

Using the string caching feature results in performance improvements, but increases memory usage slightly.

!!! note "String Caching Details"

    1. Strings are cached using a fully associative cache with a size of
    [16,384](https://github.com/pydantic/jiter/blob/5bbdcfd22882b7b286416b22f74abd549c7b2fd7/src/py_string_cache.rs#L113).
    2. Only strings where `len(string) < 64` are cached.
    3. There is some overhead to looking up the cache, which is normally worth it to avoid constructing strings.
    However, if you know there will be very few repeated strings in your data, you might get a performance boost by disabling this setting with `cache_strings=False`.
