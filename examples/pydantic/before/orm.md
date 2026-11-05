* The `from_orm` method has been deprecated; you can now just use `model_validate` (equivalent to `parse_obj` from
  Pydantic V1) to achieve something similar, as long as you've set `from_attributes=True` in the model config.
