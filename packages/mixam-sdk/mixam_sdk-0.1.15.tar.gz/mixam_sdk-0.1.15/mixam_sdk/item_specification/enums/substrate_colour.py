from __future__ import annotations

from enum import Enum

from mixam_sdk.item_specification.models.value_based import ValueBased


class SubstrateColour(ValueBased, Enum):

    NONE = 0
    BLACK = 1
    RED = 2
    ORANGE = 3
    YELLOW = 4
    GREEN = 5
    BLUE = 6
    INDIGO = 7
    VIOLET = 8
    PURPLE = 9
    PINK = 10
    TURQUOISE = 11
    SILVER = 12
    GOLD = 13
    GREY = 14
    ROSE = 15
    CREAM = 16
    DARK_GREEN = 100
    RUBY = 101
    BUTTERMILK = 102
    SAPPHIRE_BLUE = 103
    GRAPHITE = 104
    PASTEL_PINK = 105
    PASTEL_GREEN = 106
    LEAFBIRD_GREEN = 107
    PUFFIN_BLUE = 108
    SKYLARK_VIOLET = 109

    def __init__(self, value: int):
        self._value_ = value

    def get_value(self) -> int:
        return self.value
