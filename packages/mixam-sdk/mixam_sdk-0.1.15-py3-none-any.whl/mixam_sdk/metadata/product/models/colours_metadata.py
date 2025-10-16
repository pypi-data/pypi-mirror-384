from __future__ import annotations

from pydantic import BaseModel, Field, ConfigDict

from .colours_option import ColoursOption


class ColoursMetadata(BaseModel):

    colours_options: list[ColoursOption] = Field(
        alias="coloursOptions",
    )

    back_colours_options: list[ColoursOption] = Field(
        alias="backColoursOptions",
    )

    outer_cover_colours_options: list[ColoursOption] = Field(
        alias="outerCoverColoursOptions",
    )

    inner_cover_colours_options: list[ColoursOption] = Field(
        alias="innerCoverColoursOptions",
    )

    jacket_colours_options: list[ColoursOption] = Field(
        alias="jacketColoursOptions",
    )

    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore",
        frozen=True,
        strict=True,
        validate_assignment=True,
    )


__all__ = ["ColoursMetadata"]
