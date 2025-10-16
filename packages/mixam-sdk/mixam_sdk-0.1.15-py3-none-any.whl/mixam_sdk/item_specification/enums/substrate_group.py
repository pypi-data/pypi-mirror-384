from __future__ import annotations

from enum import Enum

from mixam_sdk.item_specification.models.value_based import ValueBased


class SubstrateGroup(ValueBased, Enum):

    NONE = 0
    COATED = 1
    UNCOATED = 2
    SPECIAL = 3

    def get_value(self) -> int:
        return int(self.value)
