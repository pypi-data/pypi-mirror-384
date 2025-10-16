from __future__ import annotations

from pydantic import BaseModel, Field, ConfigDict


class CustomSizeMetadata(BaseModel):

    min_width: float = Field(
        alias="minWidth",
    )

    min_height: float = Field(
        alias="minHeight",
    )

    max_width: float = Field(
        alias="maxWidth",
    )

    max_height: float = Field(
        alias="maxHeight",
    )

    size_format: str = Field(
        alias="sizeFormat",
    )

    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore",
        frozen=True,
        strict=True,
        validate_assignment=True,
    )


__all__ = ["CustomSizeMetadata"]
