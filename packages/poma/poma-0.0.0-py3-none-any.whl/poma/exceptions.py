# exceptions.py


class PomaSDKError(Exception):
    """Base class for all custom SDK errors."""


class AuthenticationError(PomaSDKError):
    """401/403 errors – invalid or missing token."""


class RemoteServerError(PomaSDKError):
    """5xx errors returned by the Poma backend."""


class InvalidInputError(PomaSDKError):
    """Raised when an unsupported *Content‑Type* is given to ``chunk_text``."""

class InvalidResponseError(PomaSDKError):
    """Raised when the server returns non-JSON or empty body."""
