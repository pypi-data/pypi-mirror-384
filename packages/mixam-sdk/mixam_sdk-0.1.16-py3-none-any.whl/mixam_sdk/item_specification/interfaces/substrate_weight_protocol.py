from __future__ import annotations

from typing import Protocol, Optional

from mixam_sdk.item_specification.models.substrate_weight import SubstrateWeight, SubstrateWeightType


class SubstrateWeightEnum(Protocol):
    def get_values(self) -> SubstrateWeight:
        ...

    def get_value(self) -> int:
        return self.get_values().value

    def get_gsm(self) -> int:
        return self.get_values().gsm

    def get_lbs(self) -> Optional[int]:
        return self.get_values().lbs

    def get_caliper(self) -> float:
        return self.get_values().caliper

    def get_weight_type(self) -> Optional[SubstrateWeightType]:
        return self.get_values().weight_type
