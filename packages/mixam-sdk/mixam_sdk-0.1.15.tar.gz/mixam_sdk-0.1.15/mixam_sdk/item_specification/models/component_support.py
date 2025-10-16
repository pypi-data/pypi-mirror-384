from __future__ import annotations

from typing import ClassVar, Dict, Annotated

from pydantic import BaseModel, Field, ConfigDict

from mixam_sdk.item_specification.enums.colours import Colours
from mixam_sdk.item_specification.enums.orientation import Orientation
from mixam_sdk.item_specification.enums.pre_drilled_holes import PreDrilledHoles
from mixam_sdk.item_specification.enums.standard_size import StandardSize
from mixam_sdk.item_specification.enums.unit_format import UnitFormat
from mixam_sdk.item_specification.interfaces.component_protocol import (
    member_meta,
    container_meta,
    LaminatedComponent as ILaminatedComponent,
    TwoSidedComponent as ITwoSidedComponent,
    FoiledComponent as IFoiledComponent,
    ShapedComponent as IShapedComponent, )
from mixam_sdk.item_specification.models.custom_size import CustomSize
from mixam_sdk.item_specification.models.embellishments import Embellishments
from mixam_sdk.item_specification.models.substrate import Substrate
from mixam_sdk.utils.enum_json import enum_by_name_or_value, enum_dump_name
from mixam_sdk.utils.utils import MM_IN_INCH


class ComponentSupport(BaseModel):

    FIELDS: ClassVar[Dict[str, str]] = {
        "format": "f",
        "standard_size": "z",
        "custom_size": "c",
        "orientation": "o",
        "colours": "c",
        "substrate": "s",
        "pre_drilled_holes": "h",
        "embellishments": "e",
    }

    component_type: None

    format: int = Field(
        default=0,
        description="DIN format value of the component.",
        json_schema_extra=member_meta(FIELDS["format"]),
    )

    standard_size: Annotated[StandardSize, enum_by_name_or_value(StandardSize), enum_dump_name] = Field(
        default=StandardSize.NONE,
        alias="standardSize",
        description="Non-DIN standard size; NONE when DIN format is used.",
        json_schema_extra=member_meta(FIELDS["standard_size"]),
    )

    custom_size: CustomSize | None = Field(
        default=None,
        alias="customSize",
        description="Custom size dimensions when present.",
        json_schema_extra=container_meta(FIELDS["custom_size"]),
    )

    orientation: Annotated[Orientation, enum_by_name_or_value(Orientation), enum_dump_name] = Field(
        default=Orientation.PORTRAIT,
        description="Orientation of the component.",
        json_schema_extra=member_meta(FIELDS["orientation"]),
    )

    colours: Annotated[Colours, enum_by_name_or_value(Colours), enum_dump_name] = Field(
        default=Colours.NONE,
        description="Printing colour type used.",
        json_schema_extra=member_meta(FIELDS["colours"]),
    )

    substrate: Substrate = Field(
        default_factory=Substrate,
        description="Substrate details of the component.",
        json_schema_extra=container_meta(FIELDS["substrate"]),
    )

    # Note: not all components support pre-drilled holes; keep optional
    pre_drilled_holes: Annotated[PreDrilledHoles | None, enum_by_name_or_value(PreDrilledHoles), enum_dump_name] = Field(
        default=PreDrilledHoles.NONE,
        alias="preDrilledHoles",
        description="Pre-drilled holes option (if supported).",
        json_schema_extra=member_meta(FIELDS["pre_drilled_holes"]),
        validation_alias="preDrilledHoles",
    )

    embellishments: Embellishments = Field(
        default_factory=Embellishments,
        description="Configured embellishments, if any.",
        json_schema_extra=container_meta(FIELDS["embellishments"]),
    )

    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore",
        frozen=False,
        strict=True,
        validate_assignment=True
    )

    def has_back(self) -> bool:
        return False

    def is_folded(self) -> bool:
        return False

    def has_custom_size(self) -> bool:
        return self.custom_size is not None

    def is_laminated_component(self) -> bool:
        return isinstance(self, ILaminatedComponent)

    def is_two_sided_component(self) -> bool:
        return isinstance(self, ITwoSidedComponent)

    def is_foiled_component(self) -> bool:
        return isinstance(self, IFoiledComponent)

    def is_shaped_component(self) -> bool:
        return isinstance(self, IShapedComponent)

    def configure_size_format(self, format_value: int) -> None:
        self.format = int(format_value)
        self.standard_size = StandardSize.NONE
        self.custom_size = None

    def configure_size_standard(self, standard_size: StandardSize) -> None:
        ss = StandardSize(standard_size)
        self.format = ss.get_format()
        self.standard_size = ss
        self.custom_size = None

    def configure_size_custom(self, custom_size: CustomSize | None) -> None:
        if custom_size is None:
            self.custom_size = None
            return
        if custom_size.unit_format == UnitFormat.IMPERIAL:
            width_mm = float(custom_size.width) * float(MM_IN_INCH)
            height_mm = float(custom_size.height) * float(MM_IN_INCH)
        else:
            width_mm = float(custom_size.width)
            height_mm = float(custom_size.height)

        from mixam_sdk.utils.utils import get_b_format_from_custom_size
        fmt = get_b_format_from_custom_size(width=width_mm, height=height_mm, size_format=UnitFormat.METRIC, is_offset_optimized=False, is_perfect_bound=False)
        self.format = int(fmt)
        self.standard_size = StandardSize.NONE
        self.custom_size = custom_size

