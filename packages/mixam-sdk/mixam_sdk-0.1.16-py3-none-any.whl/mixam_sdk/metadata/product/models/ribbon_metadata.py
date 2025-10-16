from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, Field, ConfigDict

from mixam_sdk.item_specification.enums.ribbon_colour import RibbonColour
from mixam_sdk.utils.enum_json import enum_by_name_or_value, enum_dump_name


class RibbonMetadata(BaseModel):

    ribbon_colour: Annotated[RibbonColour, enum_by_name_or_value(RibbonColour), enum_dump_name] = Field(
        alias="ribbonColour",
    )

    label: str = Field()

    colour_code: str = Field(
        alias="colourCode",
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


__all__ = ["RibbonMetadata"]
