import json
import re
import requests
from time import time

def get_client_info():
  '''Fetches the client version and build number from the HeroZero JavaScript file.'''
  url = "https://hz-static-2.akamaized.net/assets/html5/HeroZero.min.js"
  r = requests.get(url, timeout=10)
  r.raise_for_status()
  js_code = r.text

  match = re.search(r"this\.clientVersion\s*=\s*(\d+);\s*this\.buildNumber\s*=\s*(\d+);", js_code)
  if not match:
    raise RuntimeError("Could not find clientVersion/buildNumber in JS file!")

  client_version = match.group(1)
  build_number = match.group(2)

  return client_version, build_number

def calc_regen(current_value: int, last_change_ts: int, max_value: int, regen_rate: float) -> int:
  '''
  Calculate the current value of a resource based on its last change timestamp, maximum value, regeneration rate, and current value.
  '''
  if regen_rate <= 0 or max_value <= 0:
    return max_value

  minutes_passed = (time() - last_change_ts) // 60
  regenerated_amount = int(minutes_passed * regen_rate)
  new_value = current_value + regenerated_amount
  return min(new_value, max_value)

def time_left(target_ts: int) -> int:
  '''
  Returns the time left in seconds until the target timestamp.
  '''
  return max(0, target_ts - int(time()))

def str_to_array(s: str) -> list:
  if isinstance(s, str):
    try:
      return [int(x) for x in s.strip("[]").split(",") if x]
    except ValueError:
      return []
  return s

def parse_json_dict(v):
  if v is None:
    return {}
  if isinstance(v, str):
    return json.loads(v)
  return v

def wrap_in_list(v):
  if not isinstance(v, list):
    return [v]

  if all(isinstance(i, dict) and 'opponent' in i for i in v):
    return [i['opponent'] for i in v]
  return v

def round_decimal(value: float, decimals: int) -> float:
  '''
  Rounds a float to a specified number of decimal places.
  '''
  factor = 10 ** decimals
  return round(value * factor) / factor

def remove_duplicates_by_id(data: list) -> list:
  seen = set()
  unique_items = []
  for item in data:
    item_id = item.get('id')
    if item_id not in seen:
      unique_items.append(item)
      seen.add(item_id)
  return unique_items