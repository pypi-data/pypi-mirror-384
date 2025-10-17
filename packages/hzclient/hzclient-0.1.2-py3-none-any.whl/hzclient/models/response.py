from __future__ import annotations

from typing import Dict, Optional, Any


class Response:
  """Lightweight parsed API response.

  Attributes:
    status_code: HTTP status code returned by server.
    data: Parsed payload (defaults to empty dict when missing).
    error: Optional error string extracted from payload or provided directly.
  """

  def __init__(self, status_code: int, data: Optional[Dict[str, Any]] = None, error: Optional[str] = None):
    self.status_code = int(status_code)
    self.data = data.get("data", data) if data else {}
    self.error = error or (data.get("error") if data else None)

  @property
  def is_success(self) -> bool:
    return 200 <= self.status_code < 300 and not self.error