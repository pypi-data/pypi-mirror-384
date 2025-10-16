from __future__ import annotations

from enum import Enum

from mixam_sdk.item_specification.models.value_based import ValueBased


class PreDrilledHoles(ValueBased, Enum):

    NONE = 0
    ONE_HOLE_OPPOSITE_BINDING_CENTER = 1
    ONE_HOLE_TOP_CENTER = 2

    def get_value(self) -> int:
        return int(self.value)
