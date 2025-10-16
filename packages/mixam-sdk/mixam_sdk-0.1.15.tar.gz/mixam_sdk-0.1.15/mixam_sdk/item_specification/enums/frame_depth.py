from __future__ import annotations

from enum import Enum

from mixam_sdk.item_specification.models.value_based import ValueBased


class FrameDepth(ValueBased, Enum):

    UNSPECIFIED = 0
    MM_18 = 1
    MM_38 = 2

    def get_value(self) -> int:
        return int(self.value)
