from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, Field, ConfigDict

from mixam_sdk.item_specification.enums.substrate_group import SubstrateGroup
from mixam_sdk.item_specification.enums.substrate_type import SubstrateType
from mixam_sdk.utils.enum_json import enum_by_name_or_value, enum_dump_name
from .substrate_colour_metadata import SubstrateColourMetadata


class SubstrateTypeMetadata(BaseModel):

    id: int = Field()

    substrate_type: Annotated[SubstrateType, enum_by_name_or_value(SubstrateType), enum_dump_name] = Field(
        alias="substrateType",
    )

    substrate_group: Annotated[SubstrateGroup, enum_by_name_or_value(SubstrateGroup), enum_dump_name] = Field(
        alias="substrateGroup",
    )

    substrate_colours: list[SubstrateColourMetadata] = Field(
        alias="substrateColours",
    )

    allow_lamination: bool = Field(
        default=False,
        alias="allowLamination",
    )

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


__all__ = ["SubstrateTypeMetadata"]
