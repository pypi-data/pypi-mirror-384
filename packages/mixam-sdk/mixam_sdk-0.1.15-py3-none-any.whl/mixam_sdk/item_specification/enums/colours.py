from __future__ import annotations

from enum import Enum

from mixam_sdk.item_specification.models.value_based import ValueBased


class Colours(ValueBased, Enum):

    NONE = 0
    GRAYSCALE = 1
    PROCESS = 5

    def get_value(self) -> int:
        return int(self.value)
