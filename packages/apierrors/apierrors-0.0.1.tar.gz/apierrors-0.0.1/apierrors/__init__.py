__version__ = "0.0.0"

from . import status_codes as _status

__all__ = [
    "Err400",
    "HttpErr400BadRequest",
    "Err401",
    "HttpErr401Unauthorized",
    "Err403",
    "HttpErr403Forbidden",
    "Err404",
    "HttpErr404NotFound",
    "Err405",
    "HttpErr405MethodNotAllowed",
    "Err409",
    "HttpErr409Conflict",
    "Err422",
    "HttpErr422UnprocessableEntity",
]

for name in __all__:
    globals()[name] = getattr(_status, name)
