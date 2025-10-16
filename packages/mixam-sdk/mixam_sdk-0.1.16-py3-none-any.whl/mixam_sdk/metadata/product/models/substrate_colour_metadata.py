from __future__ import annotations

from typing import Annotated, Optional

from pydantic import BaseModel, Field, ConfigDict

from mixam_sdk.item_specification.enums.substrate_colour import SubstrateColour
from mixam_sdk.utils.enum_json import enum_by_name_or_value, enum_dump_name
from .substrate_weight_metadata import SubstrateWeightMetadata


class SubstrateColourMetadata(BaseModel):

    colour: Annotated[SubstrateColour, enum_by_name_or_value(SubstrateColour), enum_dump_name] = Field()

    id: int = Field()

    hex_colour: Optional[str] = Field(
        default=None,
        alias="hexColour",
    )

    label: str = Field()

    weights: list[SubstrateWeightMetadata] = Field()

    allow_printing: bool = Field(
        default=False,
        alias="allowPrinting",
    )

    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore",
        frozen=True,
        strict=True,
        validate_assignment=True,
    )


__all__ = ["SubstrateColourMetadata"]
