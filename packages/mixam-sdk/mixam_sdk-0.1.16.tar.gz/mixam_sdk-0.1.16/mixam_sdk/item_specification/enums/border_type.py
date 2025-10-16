from __future__ import annotations

from enum import Enum

from mixam_sdk.item_specification.models.value_based import ValueBased


class BorderType(ValueBased, Enum):

    WRAP_AROUND = 0
    EDGE_TO_EDGE = 1
    PADDED = 2

    def get_value(self) -> int:
        return int(self.value)
