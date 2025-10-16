from __future__ import annotations

from typing import ClassVar, Dict, Literal, Annotated

from pydantic import Field, ConfigDict

from mixam_sdk.item_specification.enums.component_type import ComponentType
from mixam_sdk.item_specification.enums.sample_pack_type import SamplePackType
from mixam_sdk.item_specification.interfaces.component_protocol import member_meta
from mixam_sdk.item_specification.models.component_support import ComponentSupport
from mixam_sdk.utils.enum_json import enum_by_name_or_value, enum_dump_name


class SamplePackComponent(ComponentSupport):

    FIELDS: ClassVar[Dict[str, str]] = {
        "sample_pack_type": "x",
    }

    component_type: Literal[ComponentType.SAMPLE_PACK] = Field(
        default=ComponentType.SAMPLE_PACK,
        alias="componentType",
        validation_alias="componentType",
        frozen=True
    )

    sample_pack_type: Annotated[SamplePackType, enum_by_name_or_value(SamplePackType), enum_dump_name] = Field(
        default=SamplePackType.PRODUCTS,
        alias="samplePackType",
        description="The type of sample pack being ordered",
        json_schema_extra=member_meta(FIELDS["sample_pack_type"]),
    )

    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore",
        frozen=False,
        strict=True,
        validate_assignment=True
    )


