from __future__ import annotations

from typing import ClassVar, Dict

from pydantic import BaseModel, Field, ConfigDict, AliasChoices

from mixam_sdk.item_specification.interfaces.component_protocol import member_meta


class Embellishments(BaseModel):

    FIELDS: ClassVar[Dict[str, str]] = {
        "spot_uv": "v",
    }

    spot_uv: bool = Field(
        default=False,
        alias="spotUv",
        description="True if the component requires Spot UV, otherwise false",
        json_schema_extra=member_meta(FIELDS["spot_uv"]),
        validation_alias=AliasChoices("spotUv", "v"),
    )

    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore",
        frozen=False,
        strict=True,
        validate_assignment=True
    )

    def has_spot_uv(self) -> bool:
        return bool(self.spot_uv)

    def set_spot_uv(self, spot_uv: bool) -> Embellishments:
        self.spot_uv = spot_uv
        return self
