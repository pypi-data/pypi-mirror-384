from __future__ import annotations

from typing import ClassVar, Dict, Literal

from pydantic import Field, ConfigDict

from mixam_sdk.item_specification.enums.component_type import ComponentType
from mixam_sdk.item_specification.interfaces.component_protocol import member_meta
from mixam_sdk.item_specification.models.two_sided_component_support import (
    TwoSidedComponentSupport,
)


class FlatComponent(TwoSidedComponentSupport):

    FIELDS: ClassVar[Dict[str, str]] = {
        "round_corners": "r",
    }

    component_type: Literal[ComponentType.FLAT] = Field(
        default=ComponentType.FLAT,
        alias="componentType",
        validation_alias="componentType",
        frozen=True
    )

    round_corners: bool = Field(
        default=False,
        alias="roundCorners",
        description="Whether the item has rounded corners.",
        json_schema_extra=member_meta(FIELDS["round_corners"]),
    )

    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore",
        frozen=False,
        strict=True,
        validate_assignment=True
    )

