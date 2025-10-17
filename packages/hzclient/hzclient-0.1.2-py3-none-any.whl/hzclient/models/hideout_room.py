from time import time

from .base import _Base


class HideoutRoom(_Base):
  id: int = 0
  identifier: str = ""
  ts_activity_end: int = 0
  ts_last_resource_change: int = 0
  level: int = 0
  status: int = 0

  current_resource_amount: int = 0
  max_resource_amount: int = 0

  @property
  def is_manually_production_room(self) -> bool:
    return self.identifier in ["attacker_production", "defender_production", "gem_production", "exchange_room", "gym", "blacksmith"]

  @property
  def is_auto_production_room(self) -> bool:
    return self.identifier in ["main_building", "glue_production", "stone_production", "xp_production"]

  @property
  def is_production_complete(self) -> bool:
    return self.ts_activity_end > 0 and time() >= self.ts_activity_end