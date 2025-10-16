from __future__ import annotations

from typing import ClassVar, Dict, Annotated

from pydantic import Field, ConfigDict

from mixam_sdk.item_specification.enums.shape import Shape
from mixam_sdk.item_specification.interfaces.component_protocol import member_meta
from mixam_sdk.item_specification.models.component_support import ComponentSupport
from mixam_sdk.utils.enum_json import enum_by_name_or_value, enum_dump_name


class ShapedComponentSupport(ComponentSupport):

    FIELDS: ClassVar[Dict[str, str]] = {
        "shape": "q",
    }

    shape: Annotated[Shape, enum_by_name_or_value(Shape), enum_dump_name] = Field(
        default=Shape.RECTANGLE,
        alias="shape",
        description="Shape of the component.",
        json_schema_extra=member_meta(FIELDS["shape"]),
    )

    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore",
        frozen=False,
        strict=True,
        validate_assignment=True
    )

