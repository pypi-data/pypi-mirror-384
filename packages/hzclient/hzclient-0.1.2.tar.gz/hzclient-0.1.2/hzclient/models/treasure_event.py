from time import time

from .base import _Base


class TreasureEvent(_Base):
  id: int = 0
  ts_reveal_item_collected: int = 0

  @property
  def can_collect_reveal_item(self) -> bool:
    return (time() - self.ts_reveal_item_collected) >= 3 * 3600 or self.ts_reveal_item_collected == 0