from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, Field, ConfigDict

from mixam_sdk.item_specification.enums.binding_type import BindingType
from mixam_sdk.item_specification.models.substrate import Substrate
from mixam_sdk.utils.enum_json import enum_by_name_or_value, enum_dump_name
from .binding_colour_option import BindingColourOption
from .colours_option import ColoursOption
from ..enums.trilean import Trilean


class BindingTypeOption(BaseModel):

    binding_type: Annotated[BindingType, enum_by_name_or_value(BindingType), enum_dump_name] = Field(
        alias="bindingType",
    )

    label: str = Field(
        alias="label",
    )

    value: int = Field(
        alias="value",
    )

    default_pages: int = Field(
        alias="defaultPages",
    )
    caliper: float = Field(
        alias="caliper",
    )

    separate_cover: Annotated[Trilean, enum_by_name_or_value(Trilean), enum_dump_name] = Field(
        alias="separateCover",
    )

    separate_cover_outer_colours_options: list[ColoursOption] = Field(
        default_factory=list,
        alias="separateCoverOuterColoursOptions",
    )

    separate_cover_inner_colours_options: list[ColoursOption] = Field(
        alias="separateCoverInnerColoursOptions",
    )

    pre_drilled_holes: Annotated[Trilean, enum_by_name_or_value(Trilean), enum_dump_name] = Field(
        alias="preDrilledHoles",
    )

    colour_options: list[BindingColourOption] = Field(
        default_factory=list,
        alias="colourOptions",
    )

    sewing: Annotated[Trilean, enum_by_name_or_value(Trilean), enum_dump_name] = Field(
        alias="sewing",
    )

    required_substrate: Substrate | None = Field(
        default=None,
        alias="requiredSubstrate",
    )

    santa_default: bool = Field(
        default=False,
        alias="santaDefault",
    )

    supports_end_papers: bool = Field(
        default=False,
        alias="supportsEndPapers",
    )

    supports_dust_jacket: bool = Field(
        default=False,
        alias="supportsDustJacket",
    )

    supports_ribbons: bool = Field(
        default=False,
        alias="supportsRibbons",
    )

    supports_head_and_tail_bands: bool = Field(
        default=False,
        alias="supportsHeadAndTailBands",
    )

    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore",
        frozen=True,
        strict=True,
        validate_assignment=True,
    )


__all__ = ["BindingTypeOption"]
