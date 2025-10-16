from __future__ import annotations

from pydantic import BaseModel, Field, ConfigDict


class LaminationOption(BaseModel):

    SAME_AS_FRONT: str = "SAME_AS_FRONT"

    lamination: str = Field()

    label: str = Field(
        default="",
    )

    value: int = Field(
        default=0,
    )

    santa_default: bool = Field(
        default=False,
        alias="santaDefault",
    )

    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore",
        frozen=True,
        strict=True,
        validate_assignment=True,
    )


__all__ = ["LaminationOption"]
