from time import time

from .base_character import BaseCharacter
from hzclient.duel_utils import simulate_duel

class Opponent(BaseCharacter):
  honor: int = 0
  league_points: int = 0
  server_id: str = ""

  attacked_count: int = 0
  max_attack_count: int = 0

  fetched: bool = False
  fetched_at: int = 0

  cached_win_chance: float | None = None
  cached_win_chance_at: int = 0

  def get_win_chance(self, character: BaseCharacter) -> float:
    '''
    Calculate the win chance against another character.
    Re-calculates if fetched_at is newer than cached_win_chance_at
    '''
    if self.cached_win_chance is not None and self.fetched_at <= self.cached_win_chance_at:
      return self.cached_win_chance

    win_chance = simulate_duel(character, self) # win chance of character against this opponent

    # Cache the result
    self.cached_win_chance = win_chance
    self.cached_win_chance_at = int(time())
    return win_chance