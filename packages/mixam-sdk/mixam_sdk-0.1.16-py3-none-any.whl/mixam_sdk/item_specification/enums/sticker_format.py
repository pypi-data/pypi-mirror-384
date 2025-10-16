from __future__ import annotations

from enum import Enum

from mixam_sdk.item_specification.models.value_based import ValueBased


class StickerFormat(ValueBased, Enum):
    SHEET = 0
    ROLL = 1

    def get_value(self) -> int:
        return int(self.value)
