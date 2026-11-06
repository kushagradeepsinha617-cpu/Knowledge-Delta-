[](){#model-before-validator}

- __*Before* validators__: are run before the model is instantiated. These are more flexible than *after* validators,
  but they also have to deal with the raw input, which in theory could be any arbitrary object.
  ```python
  from typing import Any

  from pydantic import BaseModel, model_validator


  class UserModel(BaseModel):
      username: str

      @model_validator(mode='before')
      @classmethod
      def check_card_number_not_present(cls, data: Any) -> Any:  # (1)!
          if isinstance(data, dict):  # (2)!
              if 'card_number' in data:
                  raise ValueError("'card_number' should not be included")
          return data
  ```

    1. Notice the use of [`Any`][typing.Any] as a type hint for `data`. *Before* validators take the raw input, which
       can be anything.
    2. Most of the time, the input data will be a dictionary (e.g. when calling `UserModel(username='...')`). However,
       this is not always the case. For instance, if the [`from_attributes`][pydantic.ConfigDict.from_attributes]
       configuration value is set, you might receive an arbitrary class instance for the `data` argument.
