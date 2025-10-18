"""Custom exception hierarchy for the Stegawave client."""

from __future__ import annotations

from typing import Optional


class StegawaveError(Exception):
    """Base exception for all Stegawave client errors."""

    def __init__(self, message: str, *, status_code: Optional[int] = None, payload: Optional[dict] = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload or {}


class AuthenticationError(StegawaveError):
    """Raised when API key authentication fails."""


class AuthorizationError(StegawaveError):
    """Raised when the API key lacks permission for the requested resource."""


class ValidationError(StegawaveError):
    """Raised when the API rejects a request due to invalid parameters."""


class RateLimitError(StegawaveError):
    """Raised when the API throttles the client."""


class ServerError(StegawaveError):
    """Raised when the API encounters an internal server error."""


class NetworkError(StegawaveError):
    """Raised when a network issue prevents contacting the API."""


class UnexpectedResponseError(StegawaveError):
    """Raised when the API returns an unexpected payload format."""


class ProvisioningError(StegawaveError):
    """Raised when a pipeline fails to reach the expected state."""
