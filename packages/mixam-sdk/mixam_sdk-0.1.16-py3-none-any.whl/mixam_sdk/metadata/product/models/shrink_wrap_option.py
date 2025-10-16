from __future__ import annotations

from typing import Annotated, Optional

from pydantic import BaseModel, Field, ConfigDict

from mixam_sdk.item_specification.enums.substrate_type import SubstrateType
from mixam_sdk.metadata.product.models import Capacity
from mixam_sdk.utils.enum_json import enum_by_name_or_value, enum_dump_name


class ShrinkWrapOption(BaseModel):

    label: str = Field()

    substrate_type: Optional[Annotated[SubstrateType, enum_by_name_or_value(SubstrateType), enum_dump_name]] = Field(
        default=None,
        alias="substrateType",
    )

    substrate_type_id: int = Field(
        alias="substrateTypeId",
    )

    substrate_weight_id: int = Field(
        alias="substrateWeightId",
    )

    bundle_minimum: int = Field(
        alias="bundleMinimum",
    )

    bundle_increment: int = Field(
        alias="bundleIncrement",
    )

    bundle_default: int = Field(
        alias="bundleDefault",
    )

    capacity: Capacity = Field()

    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore",
        frozen=True,
        strict=True,
        validate_assignment=True,
    )


__all__ = ["ShrinkWrapOption"]
