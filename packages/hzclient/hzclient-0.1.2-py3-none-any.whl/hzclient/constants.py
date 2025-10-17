import requests
import zlib
import json

CONSTANTS = {}

def decode_constants(data):
  try:
    decompressed = zlib.decompress(data, -zlib.MAX_WBITS)
  except zlib.error:
    decompressed = zlib.decompress(data)

  utf_str = decompressed.decode('utf-8')
  return json.loads(utf_str)


def get_constants():
  url = "https://hz-static-2.akamaized.net/assets/data/constants_json.data"
  r = requests.get(url, timeout=10)
  r.raise_for_status()
  CONSTANTS.update(decode_constants(r.content))

  # r = requests.get('https://hz-static-2.akamaized.net/assets/i18n/pt_PT/text.data', timeout=10)
  # r.raise_for_status()
  # with open('text.data', 'wb') as f:
  #   f.write(decode_constants(r.content))


get_constants()