from __future__ import annotations

from typing import ClassVar, Dict, Literal, Annotated

from pydantic import Field, ConfigDict

from mixam_sdk.item_specification.enums.component_type import ComponentType
from mixam_sdk.item_specification.enums.cover_area import CoverArea
from mixam_sdk.item_specification.interfaces.component_protocol import member_meta
from mixam_sdk.item_specification.models.two_sided_component_support import (
    TwoSidedComponentSupport,
)
from mixam_sdk.utils.enum_json import enum_by_name_or_value, enum_dump_name


class CoverComponent(TwoSidedComponentSupport):

    FIELDS: ClassVar[Dict[str, str]] = {
        "cover_area": "a"
    }

    component_type: Literal[ComponentType.COVER] = Field(
        default=ComponentType.COVER,
        alias="componentType",
        validation_alias="componentType",
        frozen=True
    )

    cover_area: Annotated[CoverArea, enum_by_name_or_value(CoverArea), enum_dump_name] = Field(
        default=CoverArea.FRONT_AND_BACK,
        alias="coverArea",
        description="The area of the cover component.",
        json_schema_extra=member_meta(FIELDS["cover_area"]),
    )

    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore",
        frozen=False,
        strict=True,
        validate_assignment=True
    )


