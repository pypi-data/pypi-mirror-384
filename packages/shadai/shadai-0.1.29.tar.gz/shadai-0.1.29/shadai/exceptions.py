"""Custom exceptions for Shadai Client."""


class ShadaiError(Exception):
    """Base exception for all Shadai client errors."""

    pass


class AuthenticationError(ShadaiError):
    """Raised when authentication fails."""

    pass


class ConnectionError(ShadaiError):
    """Raised when connection to server fails."""

    pass


class ToolNotFoundError(ShadaiError):
    """Raised when requested tool doesn't exist."""

    pass


class InvalidArgumentsError(ShadaiError):
    """Raised when tool arguments are invalid."""

    pass


class ServerError(ShadaiError):
    """Raised when server returns an error."""

    pass
