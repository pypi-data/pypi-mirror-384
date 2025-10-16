from __future__ import annotations

from enum import Enum

from mixam_sdk.item_specification.models.value_based import ValueBased


class SamplePackType(ValueBased, Enum):
    PRODUCTS = 1
    PAPER_SWATCHES = 2
    PROFESSIONAL = 3
    ULTIMATE = 4

    def get_value(self) -> int:
        return int(self.value)
