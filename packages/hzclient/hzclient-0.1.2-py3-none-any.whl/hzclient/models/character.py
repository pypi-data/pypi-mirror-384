from pydantic import computed_field, BeforeValidator
from typing import Annotated, List

from .base_character import BaseCharacter
from hzclient.constants import CONSTANTS
from hzclient.utils import calc_regen, time_left, str_to_array

class Character(BaseCharacter):
  game_currency: int = 0

  stat_points_available: int = 0

  '''
  Quest stuff
  '''

  quest_energy: int = 0
  active_quest_id: int = 0
  quest_energy_refill_amount_today: int = CONSTANTS.get("quest_max_refill_amount_per_day", 1000)

  @property
  def can_buy_energy(self) -> bool:
    '''Check if the character can buy energy based on the current game currency and refill amount.'''
    value = round(
      CONSTANTS.get("coins_per_time_base", 0)
      + CONSTANTS.get("coins_per_time_scale", 0)
      * (CONSTANTS.get("coins_per_time_level_scale", 0) * self.level) ** CONSTANTS.get("coins_per_time_level_exp", 0),
      3,
    )
    refill = int(self.quest_energy_refill_amount_today / CONSTANTS.get("quest_energy_refill_amount", 1))
    cost_factor_key = f"quest_energy_refill{refill+1}_cost_factor"
    cost = round(CONSTANTS.get(cost_factor_key, 0) * value)
    return self.quest_energy_refill_amount_today < CONSTANTS.get("quest_max_refill_amount_per_day", 200) and self.game_currency >= cost

  '''
  Training
  '''

  training_count: int = 0
  active_training_id: int = 0
  training_energy: int = 0
  max_training_energy: int = 0
  ts_last_training_finished: int = 0
  ts_last_training_energy_change: int = 0

  @computed_field
  @property
  def time_to_refresh_trainings(self) -> int:
    '''
    Returns the time left in seconds to refresh trainings list.
    '''
    return time_left(self.ts_last_training_finished + CONSTANTS.get("training_cooldown", 0))

  @computed_field
  @property
  def current_training_energy(self) -> int:
    return calc_regen(
      self.training_energy,
      self.ts_last_training_energy_change,
      self.max_training_energy,
      CONSTANTS.get("training_energy_refresh_amount_per_minute", 0)
    )

  '''
  Duel
  '''
  duel_stamina_cost: int = 0
  duel_stamina: int = 0
  ts_last_duel_stamina_change: int = 0
  max_duel_stamina: int = 0

  @computed_field
  @property
  def current_duel_stamina(self) -> int:
    return calc_regen(
      self.duel_stamina,
      self.ts_last_duel_stamina_change,
      self.max_duel_stamina,
      CONSTANTS.get(
        "duel_stamina_refresh_amount_per_minute_first_duel" \
        if self.duel_stamina <= self.duel_stamina_cost else \
        "duel_stamina_refresh_amount_per_minute"
      , 0)
    )

  '''
  League
  '''
  league_opponents: Annotated[List[int], BeforeValidator(str_to_array)] = []
  league_stamina_cost: int = 0
  league_stamina: int = 0
  ts_last_league_stamina_change: int = 0
  ts_last_league_opponents_refresh: int = 0
  max_league_stamina: int = 0
  league_fight_count: int = 0

  @computed_field
  @property
  def current_league_stamina(self) -> int:
    '''
    Returns the current league stamina, considering regeneration over time.
    '''
    return calc_regen(
      self.league_stamina,
      self.ts_last_league_stamina_change,
      self.max_league_stamina,
      CONSTANTS.get(
        "league_stamina_refresh_amount_per_minute_first_fight_booster1" \
        if self.league_stamina <= self.league_stamina_cost else \
        "league_stamina_refresh_amount_per_minute"
      , 0)
    )

  @property
  def can_fight_league(self) -> bool:
    return self.league_fight_count < CONSTANTS.get("league_max_daily_league_fights", 0) \
      and self.league_stamina >= self.league_stamina_cost

  '''
  Other stuff
  '''

  new_user_voucher_ids: Annotated[List[int], BeforeValidator(str_to_array)] = []

  '''
  Events
  '''
  treasure_event_id: int = 0