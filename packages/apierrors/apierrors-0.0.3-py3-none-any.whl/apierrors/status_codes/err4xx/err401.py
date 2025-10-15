from dataclasses import dataclass, field
from typing import final

from ...errors_models import HttpErrorEnvelope, Error


@final
@dataclass(kw_only=True)
class Err401(Error):
    """
    Ошибка аутентификации.
    Важно: клиенту часто нужны подсказки для восстановления сессии.

    Критичные поля:
      - auth_scheme: ожидаемая схема аутентификации (Bearer, Basic и т.п.).
      - token_expired: признак истечения срока действия токена.
      - scope: требуемая область/скоуп (если применимо).
    """

    code: str = field(default="UNAUTHORIZED", init=False)
    # todo: error_type может содержать auth.subcode, где subcode = причина
    error_type: str = field(default="unauthorized")
    auth_scheme: str | None = None
    token_expired: bool | None = None
    scope: str | None = None


@final
@dataclass(kw_only=True, frozen=True)
class HttpErr401Unauthorized(HttpErrorEnvelope[Err401]):
    """HTTP 401 Unauthorized envelope (status_code фиксирован)."""

    status_code: int = field(default=401, init=False)
