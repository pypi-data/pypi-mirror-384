from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, Field, ConfigDict

from mixam_sdk.item_specification.enums.end_paper_colour import EndPaperColour
from mixam_sdk.utils.enum_json import enum_by_name_or_value, enum_dump_name


class EndPaperMetadata(BaseModel):

    end_paper_colour: Annotated[EndPaperColour, enum_by_name_or_value(EndPaperColour), enum_dump_name] = Field(
        alias="endPaperColour",
    )

    label: str = Field()

    colour_code: str = Field(
        alias="colourCode",
    )

    colour_id: int = Field(
        alias="colourId",
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


__all__ = ["EndPaperMetadata"]
