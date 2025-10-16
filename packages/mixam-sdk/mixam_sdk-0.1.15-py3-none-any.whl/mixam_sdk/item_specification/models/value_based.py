from __future__ import annotations

from enum import Enum
from typing import Type, TypeVar


class ValueBased:
    def get_value(self) -> int:
        raise NotImplementedError

    @staticmethod
    def for_value(value: int, enum_cls: Type[T]) -> T:
        if not issubclass(enum_cls, Enum):
            raise TypeError(f"{enum_cls} is not an Enum")
        for constant in enum_cls:
            gv = getattr(constant, "get_value", None)
            current = gv() if callable(gv) else constant.value
            if current == value:
                return constant
        raise ValueError(f"Unrecognized value: {value} for {enum_cls.__name__}")

T = TypeVar("T", bound=Enum)

def for_value(value: int, enum_cls: Type[T]) -> T:
    if not issubclass(enum_cls, Enum):
        raise TypeError(f"{enum_cls} is not an Enum")

    for constant in enum_cls:
        gv = getattr(constant, "get_value", None)
        current = gv() if callable(gv) else constant.value
        if current == value:
            return constant
    raise ValueError(f"Unrecognized value: {value} for {enum_cls.__name__}")
