from __future__ import annotations

from typing import ClassVar, Dict, Literal, Annotated

from pydantic import Field, ConfigDict

from mixam_sdk.item_specification.enums.component_type import ComponentType
from mixam_sdk.item_specification.enums.ribbon_colour import RibbonColour
from mixam_sdk.item_specification.interfaces.component_protocol import member_meta, container_meta
from mixam_sdk.utils.enum_json import enum_by_name_or_value, enum_dump_name
from mixam_sdk.item_specification.models.binding import Binding
from mixam_sdk.item_specification.models.laminated_component_support import (
    LaminatedComponentSupport,
)


class BoundComponent(LaminatedComponentSupport):

    FIELDS: ClassVar[Dict[str, str]] = {
        "pages": "p",
        "binding": "b",
        "ribbon_colour": "n",
    }

    component_type: Literal[ComponentType.BOUND] = Field(
        default=ComponentType.BOUND,
        alias="componentType",
        validation_alias="componentType",
        frozen=True
    )

    pages: int = Field(
        default=0,
        description="Number of pages (not spreads).",
        json_schema_extra=member_meta(FIELDS["pages"]),
    )

    binding: Binding = Field(
        default_factory=Binding,
        description="Binding details.",
        json_schema_extra=container_meta(FIELDS["binding"]),
    )

    ribbon_colour: Annotated[RibbonColour, enum_by_name_or_value(RibbonColour), enum_dump_name] = Field(
        default=RibbonColour.NONE,
        alias="ribbonColour",
        description="Colour of the ribbon.",
        json_schema_extra=member_meta(FIELDS["ribbon_colour"]),
    )

    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore",
        frozen=False,
        strict=True,
        validate_assignment=True
    )


    def supports_spine(self) -> bool:
        return self.binding.type.supports_spine()
