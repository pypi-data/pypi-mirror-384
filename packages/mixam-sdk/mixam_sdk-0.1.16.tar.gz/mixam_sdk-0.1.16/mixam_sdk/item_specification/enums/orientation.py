from __future__ import annotations

from enum import Enum

from mixam_sdk.item_specification.models.value_based import ValueBased


class Orientation(ValueBased, Enum):

    PORTRAIT = 0
    LANDSCAPE = 1

    def get_value(self) -> int:
        return int(self.value)