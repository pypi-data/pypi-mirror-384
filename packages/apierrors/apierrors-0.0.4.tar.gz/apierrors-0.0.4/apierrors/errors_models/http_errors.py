from dataclasses import dataclass, field
from typing import TypeVar, Generic, Mapping, List

from .base import Error


E_co = TypeVar("E_co", bound=Error, covariant=True)

@dataclass(kw_only=True, frozen=True)
class HttpErrorEnvelope(Generic[E_co]):
    """Transport-agnostic error envelope.

    A generic container for domain errors that can be serialized and sent
    over any transport (HTTP, RPC, etc.). Stores a status code, an
    immutable collection of errors, and optional headers.

    Args:
        status_code (int): Transport/HTTP status code.
        detail (tuple[E_co, ...], optional): Immutable collection of errors.
            Defaults to an empty tuple.
        headers (Mapping[str, str] | None, optional): Additional response
            headers. Defaults to ``None``.

    Attributes:
        status_code (int): The status code that will be serialized with the envelope.
        detail (tuple[E_co, ...]): Immutable collection of domain errors.
        headers (Mapping[str, str] | None): Optional response headers.

    Examples:
        Basic usage:

        >>> env = HttpErrorEnvelope[Error](
        ...     status_code=422,
        ...     detail=(Error(...),),
        ...     headers={"X-Error": "validation"},
        ... )

        Empty envelope:

        >>> HttpErrorEnvelope[Error](status_code=500)
    """
    status_code: int
    detail: list[E_co] = field(default_factory=list)
    headers: Mapping[str, str] | None = None
