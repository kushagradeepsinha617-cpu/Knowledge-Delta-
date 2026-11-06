[](){#model-after-validator}

- __*After* validators__: run after the whole model has been validated. As such, they are defined as
  *instance* methods and can be seen as post-initialization hooks. Important note: the validated instance
  should be returned.
  ```python
  from typing_extensions import Self

  from pydantic import BaseModel, model_validator


  class UserModel(BaseModel):
      username: str
      password: str
      password_repeat: str

      @model_validator(mode='after')
      def check_passwords_match(self) -> Self:
          if self.password != self.password_repeat:
              raise ValueError('Passwords do not match')
          return self
  ```
