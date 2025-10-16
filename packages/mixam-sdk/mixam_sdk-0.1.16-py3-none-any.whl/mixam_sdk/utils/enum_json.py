from __future__ import annotations
from enum import Enum
from typing import Any
from pydantic import BeforeValidator, PlainSerializer
from mixam_sdk.item_specification.models.value_based import ValueBased

# Pydantic Can't Serialize or Deserialize Enums By Name. These Helper Function Solve This Problem

def enum_by_name_or_value(enum_cls: type[Enum]) -> Any:
    def _to_enum(v):
        if isinstance(v, enum_cls):
            return v
        if isinstance(v, str):
            try:
                return enum_cls[v]
            except KeyError as e:
                raise ValueError(f"Invalid {enum_cls.__name__} name: {v!r}") from e
        if isinstance(v, int):
            try:
                return ValueBased.for_value(v, enum_cls)
            except Exception as e:
                # Fall back to direct value matching across members
                for member in enum_cls:
                    mv = getattr(member, "get_value", None)
                    current = mv() if callable(mv) else member.value
                    if current == v:
                        return member
                raise ValueError(f"Unrecognized value: {v} for {enum_cls.__name__}") from e
        raise TypeError(f"Expected {enum_cls.__name__} name (str) or value (int), got {type(v).__name__}")
    return BeforeValidator(_to_enum)


def _enum_dump_name(e):
    if e is None:
        return None
    if isinstance(e, Enum):
        return e.name
    try:
        return e.name
    except Exception:
        return e


enum_dump_name = PlainSerializer(_enum_dump_name, return_type=str | None, when_used="json")