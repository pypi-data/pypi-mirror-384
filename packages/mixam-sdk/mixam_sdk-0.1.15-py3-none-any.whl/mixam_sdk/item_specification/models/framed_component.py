from __future__ import annotations

from typing import ClassVar, Dict, Literal

from pydantic import Field, ConfigDict
from typing_extensions import Annotated

from mixam_sdk.item_specification.enums.component_type import ComponentType
from mixam_sdk.item_specification.enums.border_type import BorderType
from mixam_sdk.item_specification.enums.frame_depth import FrameDepth
from mixam_sdk.item_specification.interfaces.component_protocol import member_meta
from mixam_sdk.item_specification.models.component_support import ComponentSupport
from mixam_sdk.utils.enum_json import enum_by_name_or_value, enum_dump_name


class FramedComponent(ComponentSupport):

    FIELDS: ClassVar[Dict[str, str]] = {
        "frame_depth": "d",
        "border": "b",
    }

    component_type: Literal[ComponentType.FRAMED] = Field(
        default=ComponentType.FRAMED,
        alias="componentType",
        validation_alias="componentType",
        frozen=True
    )

    frame_depth: Annotated[FrameDepth, enum_by_name_or_value(FrameDepth), enum_dump_name] = Field(
        default=FrameDepth.UNSPECIFIED,
        alias="frameDepth",
        description="Depth of the frame.",
        json_schema_extra=member_meta(FIELDS["frame_depth"]),
        validation_alias="d",
    )

    border: Annotated[BorderType, enum_by_name_or_value(BorderType), enum_dump_name] = Field(
        default=BorderType.WRAP_AROUND,
        alias="border",
        description="Type of border for the frame.",
        json_schema_extra=member_meta(FIELDS["border"]),
    )

    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore",
        frozen=False,
        strict=True,
        validate_assignment=True
    )



