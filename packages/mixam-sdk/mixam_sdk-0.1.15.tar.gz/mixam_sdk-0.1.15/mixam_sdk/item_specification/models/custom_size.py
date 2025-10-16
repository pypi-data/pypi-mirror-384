from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import ClassVar, Dict, Tuple, Annotated

from pydantic import BaseModel, Field, ConfigDict

from mixam_sdk.item_specification.enums.unit_format import UnitFormat
from mixam_sdk.item_specification.interfaces.component_protocol import member_meta
from mixam_sdk.utils.enum_json import enum_by_name_or_value, enum_dump_name
from mixam_sdk.utils.utils import MM_IN_INCH, get_b_format_from_custom_size


class CustomSize(BaseModel):

    CUSTOM_DIMENSION_SCALE: ClassVar[int] = 2

    FIELDS: ClassVar[Dict[str, str]] = {
        "unit_format": "u",
        "width": "w",
        "height": "h",
    }

    unit_format: Annotated[UnitFormat, enum_by_name_or_value(UnitFormat), enum_dump_name] = Field(
        default=UnitFormat.METRIC,
        alias="unitFormat",
        description="Unit format used for the custom size. METRIC (mm) is 0, IMPERIAL (in) is 1",
        json_schema_extra=member_meta(FIELDS["unit_format"]),
    )

    width: Decimal = Field(
        default_factory=lambda: Decimal("0").quantize(Decimal("0.00"), rounding=ROUND_HALF_UP),
        alias="width",
        description="Width of the custom size",
        json_schema_extra=member_meta(FIELDS["width"]),
    )

    height: Decimal = Field(
        default_factory=lambda: Decimal("0").quantize(Decimal("0.00"), rounding=ROUND_HALF_UP),
        alias="height",
        description="Height of the custom size",
        json_schema_extra=member_meta(FIELDS["height"]),
    )

    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore",
        frozen=False,
        strict=True,
        validate_assignment=True
    )

    @classmethod
    def _scale_decimal(cls, value: Decimal | int | float | str) -> Decimal:
        if not isinstance(value, Decimal):
            value = Decimal(str(value))
        if cls.CUSTOM_DIMENSION_SCALE == 0:
            return value.to_integral_value(rounding=ROUND_HALF_UP)
        return value.quantize(Decimal("0.00"), rounding=ROUND_HALF_UP)

    def model_post_init(self, __context) -> None:  # type: ignore[override]
        object.__setattr__(self, "unit_format", UnitFormat(self.unit_format))
        object.__setattr__(self, "width", self._scale_decimal(self.width))
        object.__setattr__(self, "height", self._scale_decimal(self.height))

    @staticmethod
    def select_format_value(first_edge_mm: float, second_edge_mm: float) -> int:
        return get_b_format_from_custom_size(
            width=first_edge_mm,
            height=second_edge_mm,
            size_format=UnitFormat.METRIC,
            is_offset_optimized=False,
            is_perfect_bound=False,
        )

    def to_mm(self) -> Tuple[Decimal, Decimal]:
        if self.unit_format == UnitFormat.IMPERIAL:
            factor = Decimal(str(MM_IN_INCH))
            w = (self.width * factor)
            h = (self.height * factor)
        else:
            w, h = self.width, self.height
        return self._scale_decimal(w), self._scale_decimal(h)

    @staticmethod
    def select_format_value(first_edge_mm: float, second_edge_mm: float) -> int:
        return CustomSize.select_format_value(first_edge_mm, second_edge_mm)
