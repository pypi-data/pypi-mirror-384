from __future__ import annotations

from pydantic import BaseModel, Field, ConfigDict


class CopiesMetadata(BaseModel):

    initial_value: int = Field(
        default=100,
        alias="initialValue",
    )

    step_value: int = Field(
        default=50,
        alias="stepValue",
    )

    minimum_value: int = Field(
        default=1,
        alias="minimumValue",
    )

    maximum_value: int = Field(
        default=100000,
        alias="maximumValue",
    )

    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore",
        frozen=True,
        strict=True,
        validate_assignment=True,
    )


__all__ = ["CopiesMetadata"]
