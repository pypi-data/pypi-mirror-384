from __future__ import annotations

from typing import ClassVar, Dict, Annotated

from pydantic import Field, ConfigDict

from mixam_sdk.item_specification.enums.lamination import Lamination
from mixam_sdk.item_specification.interfaces.component_protocol import member_meta
from mixam_sdk.item_specification.models.component_support import ComponentSupport
from mixam_sdk.utils.enum_json import enum_by_name_or_value, enum_dump_name


class LaminatedComponentSupport(ComponentSupport):

    FIELDS: ClassVar[Dict[str, str]] = {
        "lamination": "l",
    }

    lamination: Annotated[Lamination, enum_by_name_or_value(Lamination), enum_dump_name] = Field(
        default=Lamination.NONE,
        description="Type of lamination applied to the component.",
        json_schema_extra=member_meta(FIELDS["lamination"]),
    )

    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore",
        frozen=False,
        strict=True,
        validate_assignment=True
    )
