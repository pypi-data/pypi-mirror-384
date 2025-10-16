from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, Field, ConfigDict

from mixam_sdk.item_specification.enums.pre_drilled_holes import PreDrilledHoles
from mixam_sdk.utils.enum_json import enum_by_name_or_value, enum_dump_name


class PreDrilledHoleOption(BaseModel):

    pre_drilled_holes: Annotated[PreDrilledHoles, enum_by_name_or_value(PreDrilledHoles), enum_dump_name] = Field(
        alias="preDrilledHoles",
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


__all__ = ["PreDrilledHoleOption"]
