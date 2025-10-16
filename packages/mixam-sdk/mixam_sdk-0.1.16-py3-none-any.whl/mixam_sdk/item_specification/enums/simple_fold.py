from __future__ import annotations

from enum import Enum

from mixam_sdk.item_specification.models.value_based import ValueBased


class SimpleFold(ValueBased, Enum):

    NONE = 0
    HALF = 1
    ROLE = 2
    Z = 3
    GATE = 4
    CROSS = 5
    PARALLEL = 6
    ENVELOPE = 99

    def get_value(self) -> int:
        return int(self.value)
