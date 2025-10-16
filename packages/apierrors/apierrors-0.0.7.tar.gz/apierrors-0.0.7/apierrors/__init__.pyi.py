__version__ = "0.0.7"

from .adapters.fastapi_adapter import http_exception as fastapi_http_exception
from .status_codes import (
    Err400, HttpErr400BadRequest,
    Err401, HttpErr401Unauthorized,
    Err403, HttpErr403Forbidden,
    Err404, HttpErr404NotFound,
    Err405, HttpErr405MethodNotAllowed,
    Err409, HttpErr409Conflict,
    Err422, HttpErr422UnprocessableEntity,
)
__all__ = [
    "fastapi_http_exception",
    "Err400","HttpErr400BadRequest",
    "Err401","HttpErr401Unauthorized",
    "Err403","HttpErr403Forbidden",
    "Err404","HttpErr404NotFound",
    "Err405","HttpErr405MethodNotAllowed",
    "Err409","HttpErr409Conflict",
    "Err422","HttpErr422UnprocessableEntity",
    "__version__",
]
