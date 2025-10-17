from pydantic import BeforeValidator
from typing import Annotated

from hzclient.utils import parse_json_dict
from .base import _Base

class Voucher(_Base):
  id: int = 0
  code: str = ""
  ts_end: int = 0

  rewards: Annotated[dict, BeforeValidator(parse_json_dict)] = {}

  @property
  def type(self) -> str:
    for word in ["training", "energy"]:
      if word in self.code:
        return word
    return "unknown"
