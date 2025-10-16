from __future__ import annotations

from enum import Enum

from mixam_sdk.item_specification.models.value_based import ValueBased


class Product(ValueBased, Enum):

    BROCHURES = 1
    FLYERS = 2
    FOLDED_LEAFLETS = 3
    POSTERS = 4
    LETTERHEADS = 5
    BOOK = 7
    BUSINESS_CARDS = 8
    POSTCARDS = 9
    GREETING_CARDS = 10
    NOTE_BOOKS = 11
    COMPLIMENT_SLIPS = 12
    ENVELOPES = 13  # Deprecated
    LAYFLAT_BOOKS = 15
    WALL_CALENDARS = 16  # Deprecated (PMX)
    DESK_CALENDARS = 17  # Deprecated (PMX)
    VR_WALL_CALENDARS = 18
    VR_DESK_CALENDARS = 19
    CANVAS = 21
    DUST_JACKET = 36
    SAMPLE_PACK = 37
    STICKERS = 38

    def get_value(self) -> int:
        return int(self.value)
