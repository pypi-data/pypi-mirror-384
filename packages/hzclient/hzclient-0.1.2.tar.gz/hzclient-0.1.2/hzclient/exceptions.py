"""Custom exceptions for hzclient."""

class GameClientError(Exception):
  """Base exception for hzclient."""


class AuthError(GameClientError):
  """Authentication related errors."""


class RequestError(GameClientError):
  """Errors related to sending requests."""
