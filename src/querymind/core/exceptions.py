"""Application exceptions."""

from typing import Optional


class QueryMindError(Exception):
    """Base exception for QueryMind."""

    def __init__(self, message: str, code: Optional[str] = None) -> None:
        super().__init__(message)
        self.message = message
        self.code = code or "querymind_error"


class SecurityError(QueryMindError):
    """Raised when a security policy is violated."""


class ValidationError(QueryMindError):
    """Raised when input validation fails."""


class DatabaseError(QueryMindError):
    """Raised when a database operation fails."""


class ConnectionError(QueryMindError):
    """Raised when a database connection cannot be established."""


class NotFoundError(QueryMindError):
    """Raised when a requested resource does not exist."""


class UnauthorizedError(QueryMindError):
    """Raised when the caller is not authorized for an operation."""


class AuthenticationError(QueryMindError):
    """Raised when authentication fails or credentials are invalid."""


class TimeoutError(QueryMindError):
    """Raised when an operation exceeds its time budget."""
