from __future__ import annotations

from typing import ClassVar, Dict, Annotated

from pydantic import BaseModel, Field, ConfigDict

from mixam_sdk.item_specification.enums.substrate_design import SubstrateDesign
from mixam_sdk.item_specification.interfaces.component_protocol import member_meta
from mixam_sdk.utils.enum_json import enum_by_name_or_value, enum_dump_name


class Substrate(BaseModel):

    FIELDS: ClassVar[Dict[str, str]] = {
        "typeId": "t",
        "weightId": "w",
        "colourId": "c",
        "design": "d",
    }

    type_id: int = Field(
        default=0,
        alias="typeId",
        json_schema_extra=member_meta(FIELDS["typeId"]),
    )

    weight_id: int = Field(
        default=0,
        alias="weightId",
        json_schema_extra=member_meta(FIELDS["weightId"]),
    )

    colour_id: int = Field(
        default=0,
        alias="colourId",
        json_schema_extra=member_meta(FIELDS["colourId"]),
    )

    design: Annotated[SubstrateDesign, enum_by_name_or_value(SubstrateDesign), enum_dump_name] = Field(
        default=SubstrateDesign.NONE,
        json_schema_extra=member_meta(FIELDS["design"]),
    )

    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore",
        frozen=False,
        strict=True,
        validate_assignment=True
    )

    def __hash__(self) -> int:
        return hash((self.typeId, self.weightId, self.colourId, self.design))
