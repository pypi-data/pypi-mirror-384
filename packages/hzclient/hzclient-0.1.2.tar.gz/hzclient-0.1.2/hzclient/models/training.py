from pydantic import computed_field, BeforeValidator
from typing import Annotated

from .base import _Base
from hzclient.utils import parse_json_dict, time_left
from hzclient.enums import TrainingType

class Training(_Base):
  id: int = 0
  stat_type: TrainingType = TrainingType.NONE
  status: int = 0
  ts_end: int = 0

  energy: int = 0
  needed_energy: int = 0

  training_cost: int = 0
  claimed_stars: int = 0

  rewards_star_1: Annotated[dict, BeforeValidator(parse_json_dict)] = {}
  rewards_star_2: Annotated[dict, BeforeValidator(parse_json_dict)] = {}
  rewards_star_3: Annotated[dict, BeforeValidator(parse_json_dict)] = {}

  stat_points_star_1: int = 0
  stat_points_star_2: int = 0
  stat_points_star_3: int = 0

  @computed_field
  @property
  def time_left(self) -> int:
    return time_left(self.ts_end)

  @property
  def is_complete(self) -> bool:
    return self.claimed_stars == 3 or self.status in [3, 4]

  @computed_field
  @property
  def points(self) -> int:
    count = 0
    for i in range(1, 4):
      rewards = getattr(self, f'rewards_star_{i}', {})
      if not isinstance(rewards, dict):
        rewards = {}
      count += rewards.get("statPoints", 0) + getattr(self, f'stat_points_star_{i}', 0)
    return count

  @property
  def fitness(self) -> float:
    '''
    Calculate the fitness of the training based on its stat points per energy cost.
    Penalize high energy costs to avoid selecting to avoid choosing bad trainings.
    '''
    return self.points / ((self.training_cost+1) ** 2)
