from __future__ import annotations

from enum import Enum

from mixam_sdk.item_specification.models.value_based import ValueBased


class HeadAndTailBands(ValueBased, Enum):

    NONE = 0
    NAVY_BLUE_AND_WHITE = 1
    BLACK_AND_GREEN = 2
    RED_AND_BLACK = 3
    PURPLE_AND_WHITE = 4
    RED_AND_GREY = 5
    RED_AND_WHITE = 6
    YELLOW_AND_BROWN = 7
    DARK_BROWN_AND_WHITE = 8
    BLUE_AND_YELLOW = 9
    RED_AND_GREEN = 10
    YELLOW_AND_GREEN = 11
    BLUE_AND_WHITE = 12
    DARK_BLUE_AND_WHITE = 13
    RED_AND_YELLOW = 14
    MAROON_AND_WHITE = 15
    YELLOW_AND_BLACK = 16
    GREEN_AND_WHITE = 17
    BLACK_AND_WHITE = 18
    DARK_GREEN_AND_BLACK = 19
    DARK_GREEN_AND_WHITE = 20
    RED = 21
    BLACK = 22
    GREY = 23
    WHITE = 24
    DARK_BLUE = 25
    YELLOW = 26

    def get_value(self) -> int:
        return int(self.value)
