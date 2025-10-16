from dataclasses import dataclass, field
from typing import final

from ...errors_models import HttpErrorEnvelope, Error


@final
@dataclass(kw_only=True)
class Err409(Error):
    """
    Конфликт состояния/версии ресурса.

    Критичные поля:
      - conflict_target: что именно в конфликте (resource, field, version).
      - current_state: текущее состояние на сервере.
      - expected_state: ожидаемое клиентом состояние (для решения конфликта).
      - conflict_id: идентификатор конфликтующего объекта/версии.
      - retry_after_seconds: когда клиенту имеет смысл повторить попытку (если применимо).
    """
    code: str = field(default="CONFLICT", init=False)
    error_type: str = field(default="conflict")
    conflict_target: str | None = None
    current_state: str | None = None
    expected_state: str | None = None
    conflict_id: str | None = None
    retry_after_seconds: int | None = None


@final
@dataclass(kw_only=True, frozen=True)
class HttpErr409Conflict(HttpErrorEnvelope[Err409]):
    """HTTP 409 Conflict envelope (status_code фиксирован)."""
    status_code: int = field(default=409, init=False)