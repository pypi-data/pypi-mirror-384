from .base import _Base

class User(_Base):
  id: int = 0
  session_id: str = "0"
  premium_currency: int = 0
