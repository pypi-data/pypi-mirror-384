from dataclasses import dataclass, field
from typing import final

from ...errors_models import HttpErrorEnvelope, Error


@final
@dataclass(kw_only=True)
class Err403(Error):
    """
    Ошибка авторизации/прав доступа.

    Критичные поля:
      - resource: на какой ресурс запрещён доступ.
      - action: какое действие запрещено (read/write/delete/...).
      - permission: какого разрешения не хватает.
      - owner / subject_id: контекст субъекта или владельца ресурса (если полезно клиенту).
    """
    code: str = field(default="FORBIDDEN", init=False)
    error_type: str = field(default="forbidden")
    resource: str | None = None
    action: str | None = None
    permission: str | None = None
    owner: str | None = None
    subject_id: str | None = None


@final
@dataclass(kw_only=True, frozen=True)
class HttpErr403Forbidden(HttpErrorEnvelope[Err403]):
    """HTTP 403 Forbidden envelope (status_code фиксирован)."""
    status_code: int = field(default=403, init=False)