from __future__ import annotations
from typing import Optional, Dict, Any
from time import time
import logging

from hzclient.utils import get_client_info
from hzclient.models import Response
from .state import GameState, merge_to_state
from .session import Session


class Client:
  def __init__(self, session: Session, state: Optional[GameState] = None):
    self.session = session
    self.logged_in = False
    self.state = state or GameState()
    self.client_version, self.build_number = get_client_info()
    self.logger = logging.getLogger("hzclient")

  def call(
    self,
    action: str,
    extra_params: Optional[Dict[str, Any]] = None
  ) -> dict:
    res = self.session.request(
      action,
      self.state.user.id or 0,
      self.state.user.session_id or "0",
      self.client_version,
      self.build_number,
      extra_params or {}
    )

    if res.is_success and res.data:
      self.logger.info(f"CALL SUCCESS {action}.")
      merge_to_state(self.state, res.data)
    else:
      self.logger.warning(f"CALL FAILED {action}: {res.error}")
    return res

  def login(self, email: str, password: str) -> dict:
    if not self.call("initEnvironment", { "rct": 1 }).is_success:
      raise RuntimeError("Failed to initialize environment")
    if not self.call("initGame", { "rct": 1 }).is_success:
      raise RuntimeError("Failed to initialize game")

    res = self.call("loginUser", {
      "email": email,
      "password": password,
      "platform": "",
      "platform_user_id": "",
      "client_id": f"{self.session.config.server_id}{int(time())}",
      "app_version": self.client_version,
      "device_info": '{"language":"pt","pixelAspectRatio":1,"screenDPI":72,"screenResolutionX":1680,"screenResolutionY":1050,"touchscreenType":0,"os":"HTML5","version":"WEB 9,3,4,0"}',
      "device_id": "web",
      "rct": 1
    })

    if res.is_success:
      self.logged_in = True
    return res

  def sync_game(self, sync_type: str = "normal") -> dict:
    if sync_type == "guild" and self.state.character.guild_id != 0:
      return self.call("syncGuild")

    params = {
      "force_sync": "false",
    }

    if self.state.character.guild_id != 0:
      params[f"sync_guild{self.state.character.guild_id}"] = f"{self.state.sync_states.get(f'guild{self.state.character.guild_id}', 0)}"

    if sync_type == "full":
      if not self.state.sync_states:
        self.sync_game(sync_type="guild")
        self.sync_game(sync_type="normal")

      params["sync_server"] = f"{self.state.sync_states.get('server', 0)}"
      params[f"sync_user{self.state.user.id}"] = f"{self.state.sync_states.get(f'user{self.state.user.id}', 1)}"
      params[f"sync_character{self.state.character.id}"] = f"{self.state.sync_states.get(f'character{self.state.character.id}', 0)}"

    return self.call("syncGame", params)

  def redeem_voucher(self, voucher_code: str, redeem_later: bool=True) -> dict:
    return self.call(
      f"redeem{'UserVoucherLater' if redeem_later else 'Voucher'}",
      {"code": voucher_code}
    )

  def watch_ad(self, vid_type: int) -> Response:
    if self.state.ad_info.remaining_cooldown(vid_type) > 0:
      return Response(status_code=400, data=None, error="Cannot watch ad yet, still in cooldown.")

    res = self.call("initVideoAdvertisment", {"type": vid_type, "reference_id": self.state.character.id})
    if res.is_success:
      ad_id = res.data.get("video_advertisment_id", 0)
      self.call("finishVideoAdvertisment", {"id": ad_id, "hash": ""})
      self.state.ad_info.watch_ad(vid_type)
    return res