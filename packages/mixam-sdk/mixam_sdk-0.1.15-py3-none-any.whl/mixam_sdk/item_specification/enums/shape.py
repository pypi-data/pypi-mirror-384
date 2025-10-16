from __future__ import annotations

from enum import Enum

from mixam_sdk.item_specification.models.value_based import ValueBased


class Shape(ValueBased, Enum):
    RECTANGLE = 0
    CIRCLE = 1
    OVAL = 2
    HEART = 3
    GIFT_BOX = 4
    STAR = 5
    TREE = 6

    def get_value(self) -> int:
        return int(self.value)
