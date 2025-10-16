from __future__ import annotations

from pydantic import BaseModel, Field, ConfigDict


class Capacity(BaseModel):

    x: float = Field(
        default=0.0,
        description="Typically the left-to-right or width measurement in shop-native units."
    )

    y: float = Field(
        default=0.0,
        description="Typically the top-to-bottom or height measurement in shop-native units."
    )

    z: float = Field(
        default=0.0,
        description="Typically the depth or thickness measurement in shop-native units."
    )

    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore",
        frozen=True,
        strict=True,
    )


__all__ = ["Capacity"]
