#### Patterns / regex on strings

Pydantic V1 used Python's regex library. Pydantic V2 uses the Rust [regex crate].
This crate is not just a "Rust version of regular expressions", it's a completely different approach to regular expressions.
In particular, it promises linear time searching of strings in exchange for dropping a couple of features (namely look arounds and backreferences).
We believe this is a tradeoff worth making, in particular because Pydantic is used to validate untrusted input where ensuring things don't accidentally run in exponential time depending on the untrusted input is important.
On the flipside, for anyone not using these features complex regex validation should be orders of magnitude faster because it's done in Rust and in linear time.

If you still want to use Python's regex library, you can use the [`regex_engine`](./api/config.md#pydantic.config.ConfigDict.regex_engine) config setting.

[regex crate]: https://github.com/rust-lang/regex
