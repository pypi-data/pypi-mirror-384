from __future__ import annotations

from pydantic import BaseModel, Field, ConfigDict

from .lamination_option import LaminationOption


class LaminationMetadata(BaseModel):

    front_options: list[LaminationOption] = Field(default_factory=list, alias="frontOptions")
    cover_options: list[LaminationOption] = Field(default_factory=list, alias="coverOptions")
    back_options: list[LaminationOption] = Field(default_factory=list, alias="backOptions")
    dust_jacket_options: list[LaminationOption] = Field(default_factory=list, alias="dustJacketOptions")

    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore",
        frozen=True,
        strict=True,
        validate_assignment=True,
    )


__all__ = ["LaminationMetadata"]
