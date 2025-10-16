from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from mixam_sdk.item_specification.models.value_based import ValueBased


class SubstrateWeightType(ValueBased, Enum):
    TEXT = 0
    COVER = 1

    def get_value(self) -> int:
        return int(self.value)


@dataclass(frozen=True)
class SubstrateWeight:
    value: int
    gsm: int
    caliper: float
    lbs: Optional[int] = None
    weight_type: Optional[SubstrateWeightType] = None
