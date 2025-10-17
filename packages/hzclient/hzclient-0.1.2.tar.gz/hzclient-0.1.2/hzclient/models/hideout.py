from pydantic import computed_field

from .base import _Base


class Hideout(_Base):
  id: int = 0

  current_attacker_units: int = 0
  max_attacker_units: int = 0
  current_robot_storage_level: int = 0

  @computed_field
  @property
  def current_max_attacker_units(self) -> int:
    return self.max_attacker_units * (self.current_robot_storage_level + 1)

  current_resource_glue: int = 0
  max_resource_glue: int = 0

  current_resource_stone: int = 0
  max_resource_stone: int = 0
