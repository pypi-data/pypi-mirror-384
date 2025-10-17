from pydantic import BaseModel, ConfigDict

class _Base(BaseModel):
  model_config = ConfigDict(extra='allow', validate_assignment=True)