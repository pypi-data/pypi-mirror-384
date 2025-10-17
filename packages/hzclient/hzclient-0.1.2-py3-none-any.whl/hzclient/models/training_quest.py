from typing import Annotated
from pydantic import BeforeValidator

from .training import Training
from .character import Character
from .base import _Base
from hzclient.utils import parse_json_dict

class TrainingQuest(_Base):
  id: int = 0
  status: int = 0
  energy_cost: int = 0
  rewards: Annotated[dict, BeforeValidator(parse_json_dict)] = {}

  def fitness(self, training: Training, character: Character) -> float:
    rewards = self.rewards or {}

    # Estimate wait time to get enough energy
    if ((60 * max(0, self.energy_cost - character.current_training_energy)) + self.energy_cost) > training.time_left:
      return -1

    return rewards.get("training_progress", 0) / (self.energy_cost * 1.5)