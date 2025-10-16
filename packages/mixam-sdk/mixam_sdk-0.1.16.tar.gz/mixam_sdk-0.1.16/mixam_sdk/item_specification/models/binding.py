from __future__ import annotations

from typing import ClassVar, Dict, Annotated

from pydantic import BaseModel, Field, ConfigDict

from mixam_sdk.item_specification.enums.binding_colour import BindingColour
from mixam_sdk.item_specification.enums.binding_edge import BindingEdge
from mixam_sdk.item_specification.enums.binding_loops import BindingLoops
from mixam_sdk.item_specification.enums.binding_type import BindingType
from mixam_sdk.item_specification.enums.head_and_tail_bands import HeadAndTailBands
from mixam_sdk.item_specification.interfaces.component_protocol import member_meta
from mixam_sdk.utils.enum_json import enum_by_name_or_value, enum_dump_name


class Binding(BaseModel):

    FIELDS: ClassVar[Dict[str, str]] = {
        "type": "t",
        "edge": "e",
        "sewn": "s",
        "colour": "c",
        "loops": "l",
        "head_and_tail_bands": "b",
    }

    type: Annotated[BindingType, enum_by_name_or_value(BindingType), enum_dump_name] = Field(
        default=BindingType.STAPLED,
        description="Type of binding",
        json_schema_extra=member_meta(FIELDS["type"]),
    )

    edge: Annotated[BindingEdge, enum_by_name_or_value(BindingEdge), enum_dump_name] = Field(
        default=BindingEdge.LEFT_RIGHT,
        description="Edge where the binding is applied",
        json_schema_extra=member_meta(FIELDS["edge"]),
    )

    sewn: bool = Field(
        default=False,
        description="Whether the binding is sewn. Only applicable to case bound books",
        json_schema_extra=member_meta(FIELDS["sewn"]),
    )

    colour: Annotated[BindingColour, enum_by_name_or_value(BindingColour), enum_dump_name] = Field(
        default=BindingColour.BLACK,
        description="Colour of the binding wire",
        json_schema_extra=member_meta(FIELDS["colour"]),
    )

    loops: Annotated[BindingLoops, enum_by_name_or_value(BindingLoops), enum_dump_name] = Field(
        default=BindingLoops.TWO_LOOPS,
        description="Number of loops in the binding",
        json_schema_extra=member_meta(FIELDS["loops"]),
    )

    head_and_tail_bands: Annotated[HeadAndTailBands, enum_by_name_or_value(HeadAndTailBands), enum_dump_name] = Field(
        default=HeadAndTailBands.NONE,
        alias="headAndTailBands",
        description="Head and tail band colour for a case bound book",
        json_schema_extra=member_meta(FIELDS["head_and_tail_bands"]),
    )

    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore",
        frozen=False,
        strict=True,
        validate_assignment=True
    )

