from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, Field, ConfigDict

from mixam_sdk.item_specification.enums.colours import Colours
from mixam_sdk.utils.enum_json import enum_by_name_or_value, enum_dump_name


class ColoursOption(BaseModel):

    label: str = Field(
        default="",
    )

    colours: Annotated[Colours, enum_by_name_or_value(Colours), enum_dump_name] = Field(
        default=Colours.NONE,
    )

    santa_default: bool = Field(
        default=False,
        alias="santaDefault",
    )

    same_as_front: bool = Field(
        default=False,
        alias="sameAsFront",
    )

    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore",
        frozen=True,
        strict=True,
        validate_assignment=True,
    )


__all__ = ["ColoursOption"]
