from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone

from .mixins import ToDictMixin


def _now_iso() -> str:
    """
    Return the current moment in ISO 8601 format with UTC timezone.

    Example: '2025-10-09T12:34:56.789012+00:00'
    """
    return datetime.now(timezone.utc).isoformat()


@dataclass(kw_only=True)
class ErrorFields:
    """
    Base class for HTTP-level errors with dictionary serialization.

    Fields:
      - code (str): Machine-readable error code (e.g., 'validation_error').
      - error_type (str): Error class/type for the client (e.g., 'ValidationError').
      - message (str): Human-readable message.
      - request_id (str | None): Request/trace identifier.
      - timestamp (str): ISO-8601 creation time in UTC (autofill).
      - path (str | None): Request path (if available).
      - method (str | None): HTTP method (if available).
      - traceback (str | None): Stack trace (typically only in dev).

    Methods to implement in subclasses:
      - add_extra(): return additional fields specific to the status/type
        (e.g., 'fields' for 422, 'rate_limit' for 429, etc.).

    Serialization behavior:
      - `to_dict()` collects all dataclass fields and merges them with `extra()`.
      - Top-level keys with a None value are removed.
      - Keys from `extra()` that collide with dataclass field names are FORBIDDEN
        and will raise an error.
    """
    code: str
    error_type: str
    message: str
    request_id: str | None = None
    timestamp: str = field(default_factory=_now_iso)
    path: str | None = None
    method: str | None = None
    traceback: str | None = None


@dataclass
class Error(ErrorFields, ToDictMixin):
    """
    Concrete domain error DTO that combines the data-only fields (`ErrorFields`)
    with shallow dictionary serialization via `ToDictMixin`.

    Notes:
        - Inherits all attributes from `ErrorFields` (code, error_type, message, etc.).
        - `to_dict()` is provided by `ToDictMixin` and performs a shallow export.
        - Intended to be used as the `detail` payload in HTTP envelopes/adapters.
    """
    pass
