from __future__ import annotations

from enum import Enum

from mixam_sdk.item_specification.models.value_based import ValueBased


class SubstrateDesign(ValueBased, Enum):

    NONE = 0
    LINED = 1

    def get_value(self) -> int:
        return int(self.value)
