from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, Field, ConfigDict

from mixam_sdk.item_specification.enums.foiling_colour import FoilingColour
from mixam_sdk.item_specification.enums.lamination import Lamination
from mixam_sdk.utils.enum_json import enum_by_name_or_value, enum_dump_name


class FoilingOption(BaseModel):

    label: str = Field()

    foiling_colour: Annotated[FoilingColour, enum_by_name_or_value(FoilingColour), enum_dump_name] = Field(
        alias="foilingColour",
    )

    supported_laminations: list[Annotated[Lamination, enum_by_name_or_value(Lamination), enum_dump_name]] = Field(
        alias="supportedLaminations",
    )

    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore",
        frozen=True,
        strict=True,
        validate_assignment=True,
    )


__all__ = ["FoilingOption"]
