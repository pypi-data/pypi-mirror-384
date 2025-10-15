from __future__ import annotations
from difflib import get_close_matches
from types import ModuleType
from typing import Any, List
from typing import TYPE_CHECKING, NoReturn

"""Metaclass for static, read-only registries of constants."""
class FrozenDB(type):
    def __call__(cls, *args, **kwargs):
        raise TypeError(f"{cls.__name__} is a static registry and cannot be instantiated.")
    def __setattr__(cls, name, value):
        raise TypeError(f"{cls.__name__} is read-only; cannot set attribute '{name}'.")
    def __delattr__(cls, name):
        raise TypeError(f"{cls.__name__} is read-only; cannot delete attribute '{name}'.")

    @staticmethod
    def _default_visible(name: str, value: Any) -> bool:
        # hide private/dunder names
        if name.startswith('_'):
            return False
        # hide callable objects (functions, bound methods, etc.)

        if callable(value):
            return False
        # hide common descriptors and modules
        if isinstance(value, (staticmethod, classmethod, property, ModuleType)):
            return False
        # hide classes/types
        if isinstance(value, type):
            return False
        return True

    @classmethod
    def visible_names(mcls, cls) -> list[str]:
        return mcls._visible_names(cls)  # internal call is fine here

    @classmethod
    def _visible_names(mcls, cls) -> List[str]:
        pred = mcls._default_visible
        return [n for n, v in cls.__dict__.items() if pred(n, v)]

    def __dir__(cls):
        base = list(super().__dir__())
        constants = type(cls)._visible_names(cls)
        return sorted(set(base + constants))

if not TYPE_CHECKING:
    def _meta_getattr(cls, name: str) -> NoReturn:
        available = type(cls).visible_names(cls)
        hint = ""
        if available:
            if cand := get_close_matches(name, available, n=1, cutoff=0.6):
                hint = f" Did you mean '{cand[0]}'?"
        avail_str = ", ".join(available) if available else "<none>"
        raise AttributeError(f"{cls.__name__} has no entry '{name}'. Available: {avail_str}.{hint}")
    FrozenDB.__getattr__ = _meta_getattr  # type: ignore[attr-defined]