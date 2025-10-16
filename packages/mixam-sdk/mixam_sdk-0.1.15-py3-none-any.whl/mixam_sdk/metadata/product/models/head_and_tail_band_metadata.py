from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, Field, ConfigDict

from mixam_sdk.item_specification.enums.head_and_tail_bands import HeadAndTailBands
from mixam_sdk.utils.enum_json import enum_by_name_or_value, enum_dump_name


class HeadAndTailBandMetadata(BaseModel):

    head_and_tail_bands: Annotated[HeadAndTailBands, enum_by_name_or_value(HeadAndTailBands), enum_dump_name] = Field(
        alias="headAndTailBands",
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


__all__ = ["HeadAndTailBandMetadata"]
