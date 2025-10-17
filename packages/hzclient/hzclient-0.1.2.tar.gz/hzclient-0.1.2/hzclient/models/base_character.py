from .base import _Base


class BaseCharacter(_Base):
  id: int = 0
  name: str = ""
  level: int = 0
  guild_id: int = 0
  rank: int = 0

  # Stats
  stat_total_strength: int = 0
  stat_total_stamina: int = 0
  stat_total_critical_rating: int = 0
  stat_total_dodge_rating: int = 0
  stat_weapon_damage: int = 0

  # Base stats
  state_base_strength: int = 0
  state_base_stamina: int = 0
  state_base_critical_rating: int = 0
  state_base_dodge_rating: int = 0
