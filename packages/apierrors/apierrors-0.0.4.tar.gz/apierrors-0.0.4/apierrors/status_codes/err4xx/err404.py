from dataclasses import dataclass, field
from typing import final

from ...errors_models import HttpErrorEnvelope, Error

@final
@dataclass(kw_only=True)
class Err404(Error):
    """
    Ресурс не найден.

    Критичные поля:
      - resource: тип или путь ресурса.
      - resource_id: идентификатор искомого ресурса.
      - lookup: по какому полю/критерию велся поиск (slug, email, external_id).
    """
    code: str = field(default="NOT_FOUND", init=False)
    error_type: str = field(default="not_found")
    resource: str | None = None
    resource_id: str | None = None
    lookup: str | None = None


@final
@dataclass(kw_only=True, frozen=True)
class HttpErr404NotFound(HttpErrorEnvelope[Err404]):
    """HTTP 404 Not Found envelope (status_code фиксирован)."""
    status_code: int = field(default=404, init=False)