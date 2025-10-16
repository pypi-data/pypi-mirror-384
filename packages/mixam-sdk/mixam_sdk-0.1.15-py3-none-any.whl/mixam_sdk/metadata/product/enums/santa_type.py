from __future__ import annotations

from enum import Enum


class SantaType(Enum):
    QUOTE = "QUOTE"
    PUBLICATION = "PUBLICATION"
    PRINT_ON_DEMAND = "PRINT_ON_DEMAND"
    FOURTHWALL = "FOURTHWALL"
    ADOBE_EXPRESS = "ADOBE_EXPRESS"


__all__ = ["SantaType"]
