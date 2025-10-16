from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, Field, ConfigDict

from mixam_sdk.item_specification.enums.standard_size import StandardSize
from mixam_sdk.utils.enum_json import enum_by_name_or_value, enum_dump_name
from .folding_options import FoldingOptions


class StandardSizeMetadata(BaseModel):

    standard_size: Annotated[StandardSize, enum_by_name_or_value(StandardSize), enum_dump_name] = Field(
        alias="standardSize",
    )

    name: str = Field(
        alias="name",
    )

    santa_value: str = Field(
        alias="santaValue",
    )

    width: float = Field(
        alias="width",
    )

    height: float = Field(
        alias="height",
    )

    unit_format: int = Field(
        alias="unitFormat",
    )

    santa_default: bool = Field(
        default=False,
        alias="santaDefault",
    )

    format: int = Field(
        alias="format",
    )

    secondary_format: int = Field(
        alias="secondaryFormat",
    )

    folding_options: FoldingOptions | None = Field(
        default=None,
        alias="foldingOptions",
    )

    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore",
        frozen=True,
        strict=True,
        validate_assignment=True,
    )


__all__ = ["StandardSizeMetadata"]
