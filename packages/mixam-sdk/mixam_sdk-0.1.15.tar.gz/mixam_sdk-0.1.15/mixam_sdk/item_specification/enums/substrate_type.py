from __future__ import annotations

from enum import Enum

from mixam_sdk.item_specification.enums.substrate_group import SubstrateGroup
from mixam_sdk.item_specification.models.value_based import ValueBased


class SubstrateType(ValueBased, Enum):

    NONE = (0, SubstrateGroup.NONE)
    SILK = (1, SubstrateGroup.COATED)
    GLOSS = (2, SubstrateGroup.COATED)
    UNCOATED = (3, SubstrateGroup.UNCOATED)
    COLORPLAN = (4, SubstrateGroup.SPECIAL)
    RECYCLED_UNCOATED = (7, SubstrateGroup.UNCOATED)
    RECYCLED_NATURAL = (8, SubstrateGroup.UNCOATED)
    BLUEBACK_POSTER_PAPER = (10, SubstrateGroup.SPECIAL)
    POSTCARD_BOARD = (11, SubstrateGroup.UNCOATED)
    LINEN = (12, SubstrateGroup.SPECIAL)
    PEARL_POLAR = (16, SubstrateGroup.SPECIAL)
    PEARL_OYSTER = (17, SubstrateGroup.SPECIAL)
    UNCOATED_CREME_PAPER = (35, SubstrateGroup.UNCOATED)
    TINTORETTO_GESSO = (36, SubstrateGroup.UNCOATED)
    KRAFT = (39, SubstrateGroup.UNCOATED)
    ICE_GOLD = (41, SubstrateGroup.SPECIAL)
    FRESCO_GESSO = (42, SubstrateGroup.UNCOATED)
    RIVES_SHETLAND = (43, SubstrateGroup.UNCOATED)
    RECYCLED_SILK = (45, SubstrateGroup.COATED)
    BOOKWOVE = (55, SubstrateGroup.NONE)
    POLYESTER = (56, SubstrateGroup.NONE)
    CREME = (57, SubstrateGroup.UNCOATED)
    MATTE_PAPER = (59, SubstrateGroup.COATED)
    PREMIUM_WHITE = (60, SubstrateGroup.COATED)
    POLYFILL_BAG = (76, SubstrateGroup.NONE)
    E_PHOTO_PAPER = (77, SubstrateGroup.SPECIAL)
    E_PHOTO_SILK_LUSTRE = (78, SubstrateGroup.SPECIAL)
    ARCHIVAL_MATT = (79, SubstrateGroup.SPECIAL)
    ARCHIVAL_UNCOATED = (80, SubstrateGroup.SPECIAL)
    ARCHIVAL_TEXTURED_MATT = (81, SubstrateGroup.SPECIAL)
    PHOTO_LUSTRE = (82, SubstrateGroup.SPECIAL)
    WRAPPED_GREYBOARD = (83, SubstrateGroup.NONE)
    BUCKRAM = (84, SubstrateGroup.SPECIAL)
    LAID = (85, SubstrateGroup.UNCOATED)
    ACQUERELLO = (86, SubstrateGroup.UNCOATED)
    NETTUNO = (87, SubstrateGroup.UNCOATED)
    LUX_LAYERED_KRAFT = (88, SubstrateGroup.SPECIAL)
    LUX_LAYERED_WHITE = (89, SubstrateGroup.SPECIAL)
    ETCHING = (90, SubstrateGroup.SPECIAL)
    RAG_PEARL = (91, SubstrateGroup.SPECIAL)

    def __init__(self, value: int, group: SubstrateGroup):
        self._value_ = value
        self.group = group

    def get_value(self) -> int:
        return self.value

    def get_group(self) -> SubstrateGroup:
        return self.group
