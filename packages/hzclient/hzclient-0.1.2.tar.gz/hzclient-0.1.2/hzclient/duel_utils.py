from random import random
from typing import Dict

from hzclient.models.base_character import BaseCharacter
from hzclient.constants import CONSTANTS
from .utils import round_decimal


'''
"battle_effects": {

playata.application.data.battle.BattleEffect
'''

def _get_chance(rating_1: float, rating_2: float, vars) -> float:
  '''
  Generic crit/dodge chance formula.
  '''
  def v(idx):
    return CONSTANTS.get(vars[idx], 0)
  rating_1 /= (rating_2+1)

  if rating_1 <= 1:
    result = (rating_1 ** v(3)) * (v(1) - v(0)) + v(0)
  else:
    result = (1 - (1 / rating_1) ** v(4)) * (v(2) - v(1)) + v(1)

  return round_decimal(result, 3)

def _get_critical_chance(char1: BaseCharacter, char2: BaseCharacter) -> float:
  return _get_chance(
    char1.stat_total_critical_rating,
    char2.stat_total_critical_rating,
    [
      "battle_critical_probability_min",
      "battle_critical_probability_base",
      "battle_critical_probability_max",
      "battle_critical_probability_exp_low",
      "battle_critical_probability_exp_high"
    ]
  )

def _get_dodge_chance(char1: BaseCharacter, char2: BaseCharacter) -> float:
  return _get_chance(
    char1.stat_total_dodge_rating,
    char2.stat_total_dodge_rating,
    [
      "battle_dodge_probability_min",
      "battle_dodge_probability_base",
      "battle_dodge_probability_max",
      "battle_dodge_probability_exp_low",
      "battle_dodge_probability_exp_high"
    ]
  )

def get_combat_stats_against(char1: BaseCharacter, char2: BaseCharacter) -> Dict[str, float]:
  '''
  Get combat-related stats against a specific opponent.
  '''
  return {
    "damage": char1.stat_total_strength + char1.stat_weapon_damage, # TODO: add "missile" damage
    "health": char1.stat_total_stamina * 10,
    "critical_chance": _get_critical_chance(char1, char2),
    "dodge_chance": _get_dodge_chance(char1, char2),
  }

def _simulate_turn(attacker_stats: Dict[str, float], defender_stats: Dict[str, float]) -> float:
  '''
  Simulate a single turn in combat.
  Returns the damage dealt if the attacker hits, 0 if they miss.
  '''
  if random() > defender_stats["dodge_chance"]:
    if random() < attacker_stats["critical_chance"]:
      damage = attacker_stats["damage"] * 2
    else:
      damage = attacker_stats["damage"]
    return damage
  return 0

def simulate_duel(char1: BaseCharacter, char2: BaseCharacter, rounds: int = 300) -> float:
    """
    Estimate win chance for `char1` against `char2` using Monte Carlo simulation.
    Each duel has a 50% chance of either character starting first.
    """
    char1_stats = get_combat_stats_against(char1, char2)
    char2_stats = get_combat_stats_against(char2, char1)
    wins = 0

    for _ in range(rounds):
      hp1, hp2 = char1_stats["health"], char2_stats["health"]
      attacker, defender = (char1_stats, char2_stats) if random() < 0.5 else (char2_stats, char1_stats)

      while hp1 > 0 and hp2 > 0:
        damage = _simulate_turn(attacker, defender)
        if attacker is char1_stats:
          if (hp2 := hp2 - damage) <= 0:
            wins += 1
            break
        else:
          hp1 -= damage
        attacker, defender = defender, attacker  # swap turns

    return wins / rounds