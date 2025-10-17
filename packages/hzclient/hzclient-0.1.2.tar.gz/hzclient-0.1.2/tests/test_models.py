import json, time
from unittest.mock import MagicMock

from hzclient.state import GameState
from hzclient.client import Client
from hzclient.session import Session, Response
from hzclient.models import Config, User
from hzclient import CONSTANTS


def mock_request(action: str, *args, **kwargs) -> Response:
  with open(f"tests/data/{action}.json", "r") as f:
    payload = json.load(f)
  return Response(status_code=200, data=payload)

state = GameState()
session = Session(Config(server_id="pl1"))
client = Client(session=session, state=state)
session.request = MagicMock(side_effect=mock_request)


def test_live_reflects_current_state():
  assert state.user.id == 0
  assert state.user.session_id == "0"

  client.login(email="testuser@example.com", password="testpass")
  assert state.user.id == 288


def test_user_model():
  state.user = User(id=123, session_id="abc", premium_currency=50)
  assert state.user.id == 123
  assert state.user.session_id == "abc"
  assert state.user.premium_currency == 50

  state.user.premium_currency += 50
  assert state.user.premium_currency == 100

  state.update({"user": {"premium_currency": 200}})
  assert state.user.premium_currency == 200
  assert state.user.id == 123 # unchanged
  assert state.user.session_id == "abc" # unchanged


def test_character_model():
  assert state.character.name == "JoyfulShieldbearer"


def test_constants():
  assert "quest_energy_refill_amount" in CONSTANTS


def test_state():
  assert state.debug_field == "HelloWorld!"
  state.debug_field = "NewValue"
  assert state.debug_field == "NewValue"

  assert state.debug_dict == {
    "key1": "value1",
    "key2": 2,
    "key3": True
  }
  state.reset("debug_dict")
  assert state.debug_dict == {}


def test_quests():
  assert isinstance(state.quests, list)
  assert len(state.quests) > 0
  assert state.quests[0].id == 260403


def test_trainings():
  assert isinstance(state.trainings, list)
  assert len(state.trainings) > 0
  assert state.trainings[0].id == 50633

  state.update({
    "trainings": []
  })
  assert len(state.trainings) == 0


def test_opponents():
  state.update({
    "leaderboard_characters": [
      {
        "id": 123,
        "name": "Opponent1"
      }
    ]
  })
  assert isinstance(state.opponents, list)
  assert len(state.opponents) == 1

  state.update({
    "opponent": {
      "id": 456,
      "name": "Opponent2"
    }
  })

  assert len(state.opponents) == 2

  state.update({
    "opponent": {
      "id": 123,
      "stat_total_strength": 123
    }
  })

  assert state.opponents[0].stat_total_strength == 123


def test_opponent_simulation():
  char = {'id': 1, 'stat_total_strength': 100, 'stat_total_stamina': 100, 'stat_total_critical_rating': 50, 'stat_total_dodge_rating': 50}
  state.update({
    "character": char,
    "opponent": char
  })
  opponent = state.opponents[-1]
  assert opponent.id == 1
  assert opponent.stat_total_strength == 100

  result = opponent.get_win_chance(state.character)
  assert 0.4 <= result <= 0.6


def test_ad_info():
  assert state.ad_info is not None

  assert state.ad_info.remaining_cooldown(2) != 0
  assert state.ad_info.ts_last_update__2 > 0

  time.sleep(2)
  assert state.ad_info.remaining_cooldown(2) <= 0

  assert state.ad_info.remaining_cooldown(1) == 0
  state.ad_info.watch_ad(1)
  assert state.ad_info.remaining_cooldown(1) > 0
  assert state.ad_info.ts_last_update__1 > 0
