from __future__ import annotations

from enum import Enum

from mixam_sdk.item_specification.models.value_based import ValueBased


class BindingType(ValueBased, Enum):

    STAPLED = 0
    PERFECT = 2  # Deprecated
    PUR = 4
    CASE = 6
    WIRO = 8
    LOOP = 10  # Deprecated
    CALENDAR_WIRO = 12
    SMYTH_SEWN = 14
    COIL = 16

    def get_value(self) -> int:
        return int(self.value)

    def supports_spine(self) -> bool:
        return self in {BindingType.PERFECT, BindingType.PUR, BindingType.CASE, BindingType.SMYTH_SEWN}
