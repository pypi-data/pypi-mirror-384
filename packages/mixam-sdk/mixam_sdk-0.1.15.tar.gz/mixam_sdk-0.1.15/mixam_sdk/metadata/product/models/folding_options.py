from __future__ import annotations

from pydantic import BaseModel, Field, ConfigDict

from mixam_sdk.metadata.product.models.simple_fold_option import SimpleFoldOption


class FoldingOptions(BaseModel):

    portrait_options: list[SimpleFoldOption] = Field(
        default_factory=list,
        alias="portraitOptions",
    )

    landscape_options: list[SimpleFoldOption] = Field(
        default_factory=list,
        alias="landscapeOptions",
    )

    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore",
        frozen=True,
        strict=True,
        validate_assignment=True,
    )


__all__ = ["FoldingOptions"]
