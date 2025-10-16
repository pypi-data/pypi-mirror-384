from __future__ import annotations

from typing import ClassVar, Dict, Literal

from pydantic import Field, ConfigDict

from mixam_sdk.item_specification.enums.component_type import ComponentType
from mixam_sdk.item_specification.interfaces.component_protocol import member_meta
from mixam_sdk.item_specification.models.component_support import ComponentSupport


class ShrinkWrapComponent(ComponentSupport):

    FIELDS: ClassVar[Dict[str, str]] = {
        "bundle_size": "b",
    }

    component_type: Literal[ComponentType.SHRINK_WRAP] = Field(
        default=ComponentType.SHRINK_WRAP,
        alias="componentType",
        validation_alias="componentType",
        frozen=True
    )

    bundle_size: int = Field(
        default=0,
        alias="bundleSize",
        description="The number of items wrapped in each bundle",
        json_schema_extra=member_meta(FIELDS["bundle_size"]),
    )

    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore",
        frozen=False,
        strict=True,
        validate_assignment=True
    )


