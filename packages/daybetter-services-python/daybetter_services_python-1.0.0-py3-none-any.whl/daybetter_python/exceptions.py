"""DayBetter client exceptions."""


class DayBetterError(Exception):
    """Base exception for DayBetter client."""


class AuthenticationError(DayBetterError):
    """Authentication failed."""


class APIError(DayBetterError):
    """API request failed."""
