from __future__ import annotations

from enum import Enum

from mixam_sdk.item_specification.models.value_based import ValueBased


class RibbonColour(ValueBased, Enum):

    NONE = 0
    WHITE = 1
    CREAM = 2
    GOLD = 3
    ORANGE = 4
    RED = 5
    MAROON = 6
    PINK = 7
    PURPLE = 8
    LIGHT_BLUE = 9
    BLUE = 10
    NAVY_BLUE = 11
    GREEN = 12
    DARK_GREEN = 13
    GREY = 14
    BLACK = 15

    def get_value(self) -> int:
        return int(self.value)
