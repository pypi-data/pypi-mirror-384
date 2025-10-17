from pydantic import computed_field, BeforeValidator
from typing import Annotated

from .base import _Base
from hzclient.utils import parse_json_dict, time_left

class Quest(_Base):
  id: int = 0
  status: int = 0
  energy_cost: int = 0
  rewards: Annotated[dict, BeforeValidator(parse_json_dict)] = {}
  duration: int = 0
  ts_complete: int = 0

  @property
  def fitness(self) -> int:
    '''
    Calculate the fitness of the quest based on its xp per energy cost.
    Penalize high energy costs to avoid selecting to avoid choosing bad quests.
    '''
    return self.rewards.get("xp", 0) / (self.energy_cost * 1.5)
    # return - self.duration

  @computed_field
  @property
  def time_left(self) -> int:
    return time_left(self.ts_complete)
