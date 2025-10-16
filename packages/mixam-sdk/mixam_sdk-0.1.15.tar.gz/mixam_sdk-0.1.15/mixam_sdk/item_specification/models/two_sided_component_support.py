from __future__ import annotations

from typing import ClassVar, Dict, Annotated

from pydantic import Field, ConfigDict

from mixam_sdk.item_specification.enums.colours import Colours
from mixam_sdk.item_specification.enums.lamination import Lamination
from mixam_sdk.item_specification.interfaces.component_protocol import (
    member_meta,
    container_meta, )
from mixam_sdk.item_specification.models.foiling import Foiling
from mixam_sdk.item_specification.models.laminated_foiled_component_support import LaminatedFoiledComponentSupport
from mixam_sdk.utils.enum_json import enum_by_name_or_value, enum_dump_name


class TwoSidedComponentSupport(LaminatedFoiledComponentSupport):

    FIELDS: ClassVar[Dict[str, str]] = {
        "back_colours": "c+",
        "back_lamination": "l+",
        "back_foiling": "f+",
    }

    back_colours: Annotated[Colours, enum_by_name_or_value(Colours), enum_dump_name] = Field(
        default=Colours.NONE,
        alias="backColours",
        description="Colours on the back side of the component.",
        json_schema_extra=member_meta(FIELDS["back_colours"]),
        validation_alias="backColours",
    )

    back_lamination: Annotated[Lamination, enum_by_name_or_value(Lamination), enum_dump_name] = Field(
        default=Lamination.NONE,
        alias="backLamination",
        description="Lamination on the back side of the component.",
        json_schema_extra=member_meta(FIELDS["back_lamination"]),
        validation_alias="backLamination",
    )

    back_foiling: Foiling = Field(
        default_factory=Foiling,
        alias="backFoiling",
        description="Foiling details on the back side of the component.",
        json_schema_extra=container_meta(FIELDS["back_foiling"]),
        validation_alias="backFoiling",
    )

    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore",
        frozen=False,
        strict=True,
        validate_assignment=True
    )


    def has_back(self) -> bool:
        return self.back_colours != Colours.NONE
