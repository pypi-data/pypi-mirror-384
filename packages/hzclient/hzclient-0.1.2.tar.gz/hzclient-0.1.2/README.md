# hzclient

Simple Python client for Hero Zero game API.

## Usage

```python
from hzclient import Session, GameState, Client, Config

state = GameState()
session = Session(Config(server_id=config.client.server_id))
client = Client(session=session, state=state)

client.login(email="your_email", password="your_password")

print(state.character.name) # Name of your character

client.call("someAPIMethod", {"param1": "value1"}) # Call any API method, handles session automatically
```

## Features

- No documentation available. Read the `hzclient/state.py` file to see available attributes in `GameState`.