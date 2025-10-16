from __future__ import annotations

from enum import Enum

from mixam_sdk.item_specification.models.value_based import ValueBased


class BindingLoops(ValueBased, Enum):

    TWO_LOOPS = 0
    FOUR_LOOPS = 1

    def get_value(self) -> int:
        return int(self.value)