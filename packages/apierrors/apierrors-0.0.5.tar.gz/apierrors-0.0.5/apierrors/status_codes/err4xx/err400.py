from dataclasses import dataclass, field
from typing import final

from ...errors_models import HttpErrorEnvelope, Error


@final
@dataclass(kw_only=True)
class Err400(Error):
    """Domain error representing an HTTP 400 Bad Request."""

    code: str = field(default="BAD_REQUEST", init=False)
    error_type: str = field(default="bad_request")


@final
@dataclass(kw_only=True, frozen=True)
class HttpErr400BadRequest(HttpErrorEnvelope[Err400]):
    """HTTP 400 Bad Request envelope.

    Specialization of :class:`HttpErrorEnvelope` for 400-series validation
    or client errors. The ``status_code`` is fixed and cannot be passed to
    the constructor.

    Args:
        detail (tuple[Err400, ...], optional): Immutable collection of
            ``Err400`` errors. Defaults to an empty tuple.
        headers (Mapping[str, str] | None, optional): Additional response
            headers. Defaults to ``None``.

    Attributes:
        status_code (int): Always ``400``.
        detail (tuple[Err400, ...]): Immutable collection of 400 errors.
        headers (Mapping[str, str] | None): Optional response headers.

    Examples:
        Single error:
        >>> env = HttpErr400BadRequest(
        ...     detail=(Err400(),),
        ...     headers={"X-Error": "validation"},
        ... )

        Multiple errors:

        >>> env = HttpErr400BadRequest(
        ...     detail=(Err400(), Err400()),
        ... )
    """

    status_code: int = field(default=400, init=False)
