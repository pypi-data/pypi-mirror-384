from dataclasses import dataclass


@dataclass
class Config:
  """Configuration for an API Session.

  Fields:
    server_id: Identifier (subdomain) for the game server (required).
    impersonate: User agent or impersonation hint used by the HTTP client.
    timeout: Request timeout in seconds.
  """

  server_id: str
  impersonate: str = "chrome"
  timeout: float = 5.0

  def __post_init__(self):
    if not self.server_id or not isinstance(self.server_id, str):
      raise ValueError("server_id must be a non-empty string")
    if self.timeout <= 0:
      raise ValueError("timeout must be a positive number")
