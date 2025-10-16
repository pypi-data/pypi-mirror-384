from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, Field, ConfigDict

from mixam_sdk.item_specification.enums.binding_colour import BindingColour
from mixam_sdk.utils.enum_json import enum_by_name_or_value, enum_dump_name


class BindingColourOption(BaseModel):

    binding_colour: Annotated[BindingColour, enum_by_name_or_value(BindingColour), enum_dump_name] = Field(
        alias="bindingColour",
    )

    label: str = Field()

    value: int = Field()

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


__all__ = ["BindingColourOption"]
