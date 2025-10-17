"""Handles low-level API communication."""

import curl_cffi as requests
from hashlib import md5
import logging

from hzclient.models import *


class Session:
  """Handles low-level API communication."""

  def __init__(self, config: Config):
    self.base_url = f"https://{config.server_id}.herozerogame.com"
    self.config = config
    self.session = requests.Session()
    self.logger = logging.getLogger(self.__class__.__name__)

    # Set default headers
    self.session.headers.update({
      "origin": self.base_url,
      "referer": f"{self.base_url}/",
    })

  def _get_auth(self, action: str, user_id: int) -> str:
    """Generate authentication hash for requests."""
    s = action + "GN1al351" + str(user_id)
    return md5(s.encode("utf-8")).hexdigest()

  def request(
    self,
    action: str,
    user_id: int,
    session_id: str, 
    client_version: str,
    build_number: str,
    extra_params: dict | None
  ) -> Response:
    """Make an authenticated request to the game API."""

    params = {
      "action": action,
      "user_id": user_id,
      "user_session_id": session_id,
      "client_version": f"html5_{client_version}",
      "build_number": build_number,
      "auth": self._get_auth(action, user_id),
      "rct": 2,
      "keep_active": "true",
      "device_type": "web"
    }

    if extra_params:
      params.update(extra_params)

    try:
      response = self.session.post(
        f"{self.base_url}/request.php",
        data=params,
        timeout=self.config.timeout,
        impersonate=self.config.impersonate
      )
      response.raise_for_status()

      self.logger.debug(f"Request {action} successful")
      return Response(response.status_code, response.json())
    except Exception as e:
      self.logger.error(f"Request {action} failed: {e}")
      return Response(500, error=str(e))
