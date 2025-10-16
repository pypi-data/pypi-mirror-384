from __future__ import annotations

from enum import Enum

from mixam_sdk.item_specification.models.value_based import ValueBased


class CoverArea(ValueBased, Enum):

    FRONT_AND_BACK = 0
    FRONT_ONLY = 1

    def get_value(self) -> int:
        return int(self.value)
