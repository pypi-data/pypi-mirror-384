from __future__ import annotations

from enum import Enum

from mixam_sdk.item_specification.models.value_based import ValueBased


class Lamination(ValueBased, Enum):

    NONE = (0, False)
    MATT = (5, False)
    GLOSS = (4, False)
    SOFT = (6, False)
    UV_MATT = (7, False)
    UV_GLOSS = (8, False)
    SPOT_UV_MATT = (9, True)
    SPOT_UV_GLOSS = (10, True)
    SPOT_3D_UV_MATT = (11, True)
    SPOT_3D_UV_GLOSS = (12, True)
    MATT_SPOT_UV = (14, True)
    MATT_ANTI_SCUFF = (15, False)

    def __init__(self, value: int, requires_spot_plate: bool = False) -> None:
        self._value_: int = value
        self._requires_spot_plate: bool = requires_spot_plate

    def get_value(self) -> int:
        return self._value_

    @property
    def requires_spot_plate(self) -> bool:
        return self._requires_spot_plate
