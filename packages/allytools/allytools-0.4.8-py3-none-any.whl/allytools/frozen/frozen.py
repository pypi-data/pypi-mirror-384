from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Mapping, Dict, Type
import numpy as np
from .npz import as_npz

class Frozen(ABC):
    __slots__ = ()
    _registry: Dict[str, Type["Frozen"]] = {}
    def __init__(self, *args, **kwargs) -> None:
        raise TypeError(f"Direct instantiation of {self.__class__.__name__} is not allowed. "
                        "Use the class method create(...) instead.")

    @classmethod
    def _create(cls, /, **fields: Any):
        self = object.__new__(cls)
        for k, v in fields.items():
            object.__setattr__(self, k, v)
        post_init = getattr(self, "__post_init__", None)
        if callable(post_init):
            post_init()
        return self

    @classmethod
    @abstractmethod
    def create(cls, *args, **kwargs) -> "Frozen":
        raise NotImplementedError

    @classmethod
    def register(cls, name: str | None = None):
        def _decorator(sub: Type["Frozen"]) -> Type["Frozen"]:
            cls._registry[name or sub.__name__] = sub
            return sub
        return _decorator

    def to_npz(self) -> Mapping[str, Any]:
        mapping: dict[str, Any] = {"__class__": np.array(self.__class__.__name__, dtype=np.str_)}

        attrs: list[str] = []
        if hasattr(self, "__dataclass_fields__"):
            attrs = list(getattr(self, "__dataclass_fields__").keys())
        elif hasattr(self, "__slots__"):
            slots = getattr(self, "__slots__")
            attrs = list(slots if isinstance(slots, (list, tuple)) else [slots])

        for name in attrs:
            mapping[name] = as_npz(getattr(self, name))
        return mapping

    @classmethod
    def load_from_npz(cls, npz: Mapping[str, Any]) -> "Frozen":
        if "__class__" not in npz:
            raise ValueError("NPZ mapping is missing '__class__' metadata.")
        class_name = str(np.asarray(npz["__class__"]))
        sub = cls._registry.get(class_name)
        if sub is None:
            raise ValueError(f"Unknown container class '{class_name}'. " f"Registered: {sorted(cls._registry.keys())}")
        if hasattr(sub, "from_npz"):
            return sub.from_npz(npz)  # call from_npz from subclass
        fields = {k: v for k, v in npz.items() if k != "__class__"}
        for k, v in list(fields.items()):
            if isinstance(v, np.ndarray) and v.shape == ():
                fields[k] = v.item()
        return sub._create(**fields)

    @staticmethod
    def scalar(a: Any) -> Any:
        return a.item() if isinstance(a, np.ndarray) and getattr(a, "shape", None) == () else a
