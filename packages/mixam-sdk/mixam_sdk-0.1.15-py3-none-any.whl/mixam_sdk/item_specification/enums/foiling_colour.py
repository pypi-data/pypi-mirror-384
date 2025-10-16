from __future__ import annotations

from enum import Enum
from typing import Optional


class FoilingColour(Enum):

    GOLD = ("g", 1)
    SILVER = ("s", 2)
    COPPER = ("c", 3)
    RED = ("r", 4)
    BLUE = ("b", 5)
    GREEN = ("e", 6)

    def __init__(self, foiling_colour: str, id: int):
        self._foiling_colour = foiling_colour
        self._id = id

    @property
    def foiling_colour(self) -> str:
        return self._foiling_colour

    @property
    def id(self) -> int:
        return self._id

    @classmethod
    def from_value(cls, value: int) -> Optional["FoilingColour"]:
        return next((c for c in cls if c.id == value), None)

    @classmethod
    def from_foiling_colour_value(cls, value: str) -> Optional["FoilingColour"]:
        return next((c for c in cls if c.foiling_colour == value), None)
