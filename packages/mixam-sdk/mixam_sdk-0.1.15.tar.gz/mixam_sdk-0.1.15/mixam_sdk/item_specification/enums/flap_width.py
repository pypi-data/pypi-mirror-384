from __future__ import annotations

from enum import Enum

from mixam_sdk.item_specification.models.value_based import ValueBased


class FlapWidth(ValueBased, Enum):

    AUTOMATIC = 0
    CUSTOM = 1
    MM_60 = 10
    MM_80 = 20
    IN_2_5 = 110
    IN_3_5 = 120
    PERCENT_50 = 210

    def get_value(self) -> int:
        return int(self.value)
