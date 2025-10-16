from __future__ import annotations

from typing import ClassVar, Dict, Literal, Annotated

from pydantic import Field, ConfigDict

from mixam_sdk.item_specification.enums.component_type import ComponentType
from mixam_sdk.item_specification.enums.sticker_format import StickerFormat
from mixam_sdk.item_specification.interfaces.component_protocol import member_meta
from mixam_sdk.item_specification.models.two_sided_component_support import (
    TwoSidedComponentSupport,
)
from mixam_sdk.item_specification.models.shaped_component_support import (
    ShapedComponentSupport,
)
from mixam_sdk.utils.enum_json import enum_by_name_or_value, enum_dump_name


class StickerComponent(ShapedComponentSupport, TwoSidedComponentSupport):

    FIELDS: ClassVar[Dict[str, str]] = {
        "round_corners": "r",
        "sticker_format": "k",
    }

    component_type: Literal[ComponentType.STICKER] = Field(
        default=ComponentType.STICKER,
        alias="componentType",
        validation_alias="componentType",
        frozen=True,
    )

    round_corners: bool = Field(
        default=False,
        alias="roundCorners",
        description="Indicates if the sticker has round corners.",
        json_schema_extra=member_meta(FIELDS["round_corners"]),
    )

    sticker_format: Annotated[StickerFormat, enum_by_name_or_value(StickerFormat), enum_dump_name] = Field(
        default=StickerFormat.SHEET,
        alias="stickerFormat",
        description="Format of the sticker.",
        json_schema_extra=member_meta(FIELDS["sticker_format"])
    )

    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore",
        frozen=False,
        strict=True,
        validate_assignment=True,
    )
