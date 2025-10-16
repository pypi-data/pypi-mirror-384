from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, Field, ConfigDict

from mixam_sdk.item_specification.enums.frame_depth import FrameDepth
from mixam_sdk.utils.enum_json import enum_by_name_or_value, enum_dump_name


class FrameDepthOption(BaseModel):

    frame_depth: Annotated[FrameDepth, enum_by_name_or_value(FrameDepth), enum_dump_name] = Field(
        alias="frameDepth",
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


__all__ = ["FrameDepthOption"]
