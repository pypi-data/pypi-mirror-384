from dataclasses import dataclass, field
from typing import Mapping, Any, final
from ...errors_models import HttpErrorEnvelope, Error


@final
@dataclass(kw_only=True)
class Err422(Error):
    """
    Валидационная ошибка, совместимая по форме с FastAPI.

    Поля (аналогично FastAPI):
      - loc: путь до проблемного поля/части запроса
              (например: ("body", "items", 0, "price") или ("query", "limit")).
      - ctx: произвольный контекст для построения сообщения (expected, limit_value и т.п.).

    Примечание:
      - message — это человекочитаемый текст (аналог FastAPI "msg").
    """

    code: str = field(default="UNPROCESSABLE_ENTITY", init=False)
    error_type: str = field(default="validation_error")
    loc: tuple[str | int, ...] = field(default_factory=tuple)
    ctx: Mapping[str, Any] | None = None


@final
@dataclass(kw_only=True, frozen=True)
class HttpErr422UnprocessableEntity(HttpErrorEnvelope[Err422]):
    """HTTP 422 Unprocessable Entity envelope (status_code фиксирован)."""

    status_code: int = field(default=422, init=False)
