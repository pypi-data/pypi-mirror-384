from __future__ import annotations
from time import time
from typing import ClassVar

from pydantic import model_validator
from .base import _Base

class AdInfo(_Base):
  remaining_video_advertisment_cooldown__1: int = 0
  ts_last_update__1: int = 0
  video_advertisment_blocked_time__1: int = 0

  remaining_video_advertisment_cooldown__2: int = 0
  ts_last_update__2: int = 0
  video_advertisment_blocked_time__2: int = 0

  remaining_video_advertisment_cooldown__3: int = 0
  ts_last_update__3: int = 0
  video_advertisment_blocked_time__3: int = 0

  remaining_video_advertisment_cooldown__4: int = 0
  ts_last_update__4: int = 0
  video_advertisment_blocked_time__4: int = 0

  remaining_video_advertisment_cooldown__5: int = 0
  ts_last_update__5: int = 0
  video_advertisment_blocked_time__5: int = 0

  remaining_video_advertisment_cooldown__6: int = 0
  ts_last_update__6: int = 0
  video_advertisment_blocked_time__6: int = 0

  remaining_video_advertisment_cooldown__7: int = 0
  ts_last_update__7: int = 0
  video_advertisment_blocked_time__7: int = 0

  remaining_video_advertisment_cooldown__8: int = 0
  ts_last_update__8: int = 0
  video_advertisment_blocked_time__8: int = 0

  # Utility: field-name templates (not serialized)
  _CD_FMT: ClassVar[str] = "remaining_video_advertisment_cooldown__{}"
  _TS_FMT: ClassVar[str] = "ts_last_update__{}"
  _BLK_FMT: ClassVar[str] = "video_advertisment_blocked_time__{}"

  def remaining_cooldown(self, ad_type: int) -> int:
    """
    Return remaining cooldown seconds for `ad_type` in real time,
    using the stored remaining value and the last-update timestamp.
    """
    cd = getattr(self, self._CD_FMT.format(ad_type), 0)
    ts = getattr(self, self._TS_FMT.format(ad_type), 0)
    if cd <= 0 or ts <= 0:
      return max(0, cd)
    elapsed = int(time()) - ts
    return max(0, cd - elapsed)

  def blocked_time(self, ad_type: int) -> int:
    """Return the current blocked time seconds for `ad_type`."""
    return getattr(self, self._BLK_FMT.format(ad_type), 0)

  def watch_ad(self, ad_type: int) -> None:
    """
    Start (or refresh) the cooldown to equal the current blocked-time for `ad_type`,
    and stamp the last-update to now.
    """
    blocked = self.blocked_time(ad_type)
    setattr(self, self._CD_FMT.format(ad_type), int(blocked))
    setattr(self, self._TS_FMT.format(ad_type), int(time()))

  @model_validator(mode="after")
  def _stamp_ts_for_positive_cooldowns(self):
    now = int(time())
    for i in range(1, 9):
      cd = getattr(self, self._CD_FMT.format(i), 0)
      ts = getattr(self, self._TS_FMT.format(i), 0)
      if cd > 0 and ts <= 0:
        object.__setattr__(self, self._TS_FMT.format(i), now)
    return self