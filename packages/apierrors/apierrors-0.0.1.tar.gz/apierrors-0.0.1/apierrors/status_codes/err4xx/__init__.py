from importlib import import_module

CODES = {
    400: "BadRequest",
    401: "Unauthorized",
    403: "Forbidden",
    404: "NotFound",
    405: "MethodNotAllowed",
    409: "Conflict",
    422: "UnprocessableEntity",
}

__all__ = []

for code, reason in CODES.items():
    mod = import_module(f".err{code}", __name__)
    err_name = f"Err{code}"
    http_name = f"HttpErr{code}{reason}"

    globals()[err_name] = getattr(mod, err_name)
    globals()[http_name] = getattr(mod, http_name)

    __all__.extend([err_name, http_name])
