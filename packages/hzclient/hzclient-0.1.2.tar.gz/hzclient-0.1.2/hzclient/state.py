from __future__ import annotations
from typing import Any, Dict, List, Annotated
from pydantic import AliasChoices, Field, BeforeValidator
from jsonmerge import Merger

from hzclient.models import *
from hzclient.models.base import _Base
from hzclient.utils import wrap_in_list, remove_duplicates_by_id


DEFAULT_SCHEMA = {
  "mergeStrategy": "objectMerge",
  "properties": {
    "opponents": {
      "mergeStrategy": "arrayMergeById",
      "mergeOptions": {"idRef": "id"}
    },
    "hideout_rooms": {
      "mergeStrategy": "arrayMergeById",
      "mergeOptions": {"idRef": "id"}
    },
    "daily_bonus_rewards": {
      "mergeStrategy": "append"
    },
  },
}


def merge_to_state(model: GameState, data: Dict) -> None:
  """
  Merge data into the game state.
  """

  # Special handling for lists to avoid duplicates
  if "hideout_rooms" in data:
    data["hideout_rooms"] = remove_duplicates_by_id(data["hideout_rooms"])

  patch_model = model.__class__.model_validate(data)
  payload = patch_model.model_dump(exclude_unset=True, by_alias=False, include=patch_model.model_fields_set)

  field_names = model.__class__.model_fields.keys()
  current = model.model_dump(by_alias=False, include={name: True for name in field_names})

  merged = Merger(DEFAULT_SCHEMA).merge(current, payload)

  updated = model.__class__.model_validate(merged)
  model.__dict__.update(updated.__dict__)


class GameState(_Base):
  """
  Static game state with explicit blocks.
  """
  debug_field: str = ""
  debug_dict: Dict[str, Any] = Field(default_factory=dict)

  user: User = User()
  character: Character = Character()

  # Quests
  quest: Quest = Quest()
  quests: List[Quest] = []

  # Trainings
  training: Training = Field(default_factory=Training)
  training_quests: list[TrainingQuest] = []
  trainings: list[Training] = []

  # Battles
  opponents: Annotated[list[Opponent], BeforeValidator(wrap_in_list)] = Field(
    default=[],
    validation_alias=AliasChoices("leaderboard_characters", "opponents", "requested_character", "league_opponents", "opponent"),
  )

  # Hideout
  hideout: Hideout = Field(default_factory=Hideout)
  hideout_rooms: Annotated[list[HideoutRoom], BeforeValidator(wrap_in_list)] = Field(
    default=[],
    validation_alias=AliasChoices("hideout_rooms", "hideout_room")
  )

  # Resources
  sync_states: Dict[str, Any] = Field(default_factory=dict)
  daily_login_bonus_rewards: dict = Field(default_factory=dict)

  vouchers: list[Voucher] = Field(
    default=[],
    validation_alias=AliasChoices("vouchers", "user_vouchers")
  )

  daily_bonus_rewards: Annotated[list[dict], BeforeValidator(wrap_in_list)] = Field(
    default=[],
    validation_alias=AliasChoices("daily_bonus_rewards", "daily_bonus_reward"),
  )

  max_characters: int = Field(1, description="Number of characters in the leaderboard")

  ad_info: AdInfo = Field(default_factory=AdInfo, validation_alias=AliasChoices("advertisment_info", "ad_info"))

  # Events
  treasure_event: TreasureEvent = Field(default_factory=TreasureEvent)

  # Functions
  def update(self, data: Dict) -> None:
    """
    Update the game state with new data.
    """
    merge_to_state(self, data)

  def reset(self, key: str) -> None:
    """
    Reset a specific part of the game state to its default value.
    """
    if key in self.__class__.model_fields:
      default_value = self.__class__.model_fields[key].default
      if default_value is None and self.__class__.model_fields[key].default_factory is not None:
        default_value = self.__class__.model_fields[key].default_factory()
      setattr(self, key, default_value)
    else:
      raise KeyError(f"Key '{key}' not found in GameState")
