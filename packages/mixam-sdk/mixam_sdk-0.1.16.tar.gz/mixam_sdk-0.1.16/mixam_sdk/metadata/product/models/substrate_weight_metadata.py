from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, Field, ConfigDict

from mixam_sdk.metadata.product.enums.weight_unit import WeightUnit
from mixam_sdk.metadata.product.models import PageCountMetadata
from mixam_sdk.utils.enum_json import enum_by_name_or_value, enum_dump_name


class SubstrateWeightMetadata(BaseModel):

    id: int = Field()

    weight: int = Field()

    gsm: int = Field()

    caliper: float = Field()

    unit: Annotated[WeightUnit, enum_by_name_or_value(WeightUnit), enum_dump_name] = Field()

    label: str = Field()

    santa_default: bool = Field(
        default=False,
        alias="santaDefault",
    )

    page_counts: list[PageCountMetadata] = Field(
        alias="pageCounts",
    )

    supports_lamination: bool = Field(
        default=False,
        alias="supportsLamination",
    )

    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore",
        frozen=True,
        strict=True,
        validate_assignment=True,
    )


__all__ = ["SubstrateWeightMetadata"]
