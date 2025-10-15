from typing import TypeVar, NoReturn

from fastapi import HTTPException

from ..errors_models import Error, HttpErrorEnvelope

E_co = TypeVar("E_co", bound=Error, covariant=True)


def http_exception(
        *,
        error: HttpErrorEnvelope,
) -> NoReturn:
    """
    Build FastAPI HTTPException using our envelope shape inside `detail`.

    - Converts `detail` tuple/iterable into a list
    - Dataclass errors are converted with `asdict`
    - Passes `headers` both in HTTPException(headers=...) and inside the body for convenience

    The response body will look like:
    {
      "detail": {
        "status_code": <int>,
        "detail": [ <error dicts> ],
        "headers": { ... } | null
      }
    }
    """
    status_code = error.status_code
    detail = error.detail
    headers = error.headers

    return HTTPException(
        status_code=status_code,
        detail=[err.to_dict(exclude_none=True) for err in detail],
        headers=dict(headers) if headers else None,
    )
