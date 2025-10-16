from __future__ import annotations

from dataclasses import is_dataclass, fields, dataclass
from typing import Dict, Any


def _compact_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    """
    Remove keys with a value of None at the TOP LEVEL only.
    """
    if not isinstance(d, dict):
        raise TypeError(f"_compact_dict awaits dict type but got {type(d)}")

    return {k: v for k, v in d.items() if v is not None}


class ToDictMixin:
    """
    Reusable mixin that serializes a dataclass instance to a plain dictionary.

    This mixin inspects the dataclass fields of the concrete subclass and
    builds a mapping of {field_name: value}. It optionally removes top-level
    keys whose values are None to keep payloads compact.

    Notes:
        - Works only with dataclass *instances*; otherwise a TypeError is raised.
        - This is a shallow (top-level) serialization. Nested objects are
          returned as-is unless they are already plain types.

    Example:
        @dataclass
        class User(ToDictMixin):
            id: int
            name: str
            email: str | None = None

        User(1, "Alice").to_dict()                # {'id': 1, 'name': 'Alice'}
        User(1, "Alice", None).to_dict()          # {'id': 1, 'name': 'Alice'}
        User(1, "Alice", None).to_dict(False)     # {'id': 1, 'name': 'Alice', 'email': None}
    """
    def to_dict(self: dataclass, *, exclude_none: bool = True) -> Dict[str, Any]:
        """
        Convert the dataclass instance into a dictionary.

        Args:
            exclude_none: If True (default), drop keys whose values are None
                at the top level of the resulting dictionary.

        Returns:
            A dictionary with one entry per dataclass field.

        Raises:
            TypeError: If called on a non-dataclass instance.
        """
        if not is_dataclass(self):
            raise TypeError(
                f"ToDictMixin awaits dataclass but got {type(self).__name__}"
            )

        base = {f.name: getattr(self, f.name) for f in fields(self)}
        return _compact_dict(base) if exclude_none else base
