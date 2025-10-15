from dataclasses import dataclass, field
from typing import final, Sequence

from ...errors_models import HttpErrorEnvelope, Error

@final
@dataclass(kw_only=True)
class Err405(Error):
    """
    Метод не поддерживается для ресурса.

    Критичные поля:
      - method: какой метод был использован.
      - allowed_methods: какие методы разрешены (дублирует заголовок Allow).
    """
    code: str = field(default="METHOD_NOT_ALLOWED", init=False)
    error_type: str = field(default="method_not_allowed")
    method: str | None = None
    allowed_methods: Sequence[str] = field(default_factory=tuple)


@final
@dataclass(kw_only=True, frozen=True)
class HttpErr405MethodNotAllowed(HttpErrorEnvelope[Err405]):
    """
    HTTP 405 Method Not Allowed envelope.
    Рекомендуется дополнительно выставлять заголовок 'Allow' в headers.
    """
    status_code: int = field(default=405, init=False)
