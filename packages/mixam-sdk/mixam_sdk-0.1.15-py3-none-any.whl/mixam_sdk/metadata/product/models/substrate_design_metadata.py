from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, Field, ConfigDict

from mixam_sdk.item_specification.enums.substrate_design import SubstrateDesign
from mixam_sdk.utils.enum_json import enum_by_name_or_value, enum_dump_name


class SubstrateDesignMetadata(BaseModel):

    substrate_design: Annotated[SubstrateDesign, enum_by_name_or_value(SubstrateDesign), enum_dump_name] = Field(
        alias="substrateDesign",
    )

    label: str = Field()

    santa_default: bool = Field(
        default=False,
        alias="santaDefault",
    )

    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore",
        frozen=True,
        strict=True,
        validate_assignment=True,
    )


__all__ = ["SubstrateDesignMetadata"]
