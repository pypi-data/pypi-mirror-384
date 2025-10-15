from importlib import import_module

_SUBPKGS = ("err4xx",)

__all__ = []

for pkg in _SUBPKGS:
    mod = import_module(f".{pkg}", __name__)
    names = getattr(mod, "__all__", ())
    for n in names:
        globals()[n] = getattr(mod, n)
    __all__.extend(names)


def __dir__():
    return sorted(__all__)
