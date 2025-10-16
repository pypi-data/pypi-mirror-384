from __future__ import annotations

from typing import ClassVar, Dict, Iterable, List

from pydantic import BaseModel, Field, ConfigDict

from mixam_sdk.item_specification.interfaces.component_protocol import member_meta


class Foiling(BaseModel):

    FIELDS: ClassVar[Dict[str, str]] = {
        "gold": "g",
        "silver": "s",
        "copper": "c",
        "red": "r",
        "blue": "b",
        "green": "e",
    }

    gold: bool = Field(
        False,
        description="Indicates if gold foiling is applied.",
        json_schema_extra=member_meta(FIELDS["gold"])
    )
    silver: bool = Field(
        False,
        description="Indicates if silver foiling is applied.",
        json_schema_extra=member_meta(FIELDS["silver"])
    )
    copper: bool = Field(
        False,
        description="Indicates if copper foiling is applied.",
        json_schema_extra=member_meta(FIELDS["copper"])
    )
    red: bool = Field(
        False,
        description="Indicates if red foiling is applied.",
        json_schema_extra=member_meta(FIELDS["red"])
    )
    blue: bool = Field(
        False,
        description="Indicates if blue foiling is applied.",
        json_schema_extra=member_meta(FIELDS["blue"])
    )
    green: bool = Field(
        False,
        description="Indicates if green foiling is applied.",
        json_schema_extra=member_meta(FIELDS["green"])
    )

    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore",
        frozen=False,
        strict=True,
        validate_assignment=True
    )

    def get_value(self) -> str:
        active: List[str] = []
        for attr, code in self.FIELDS.items():
            if getattr(self, attr):
                active.append(code)
        return ",".join(active)

    def set_value(self, foiling_colours: str) -> Foiling:
        want: Iterable[str] = []
        if foiling_colours:
            want = (c.strip() for c in foiling_colours.split(","))
        wanted = {c for c in want if c in self.FIELDS.values()}

        for attr, code in self.FIELDS.items():
            setattr(self, attr, code in wanted)
        return self

    def has_foiling(self) -> bool:
        return any(getattr(self, attr) for attr in self.FIELDS.keys())
