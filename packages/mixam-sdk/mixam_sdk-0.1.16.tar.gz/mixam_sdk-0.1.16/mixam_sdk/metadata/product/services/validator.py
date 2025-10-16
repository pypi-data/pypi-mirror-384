from __future__ import annotations

from typing import Dict, TYPE_CHECKING

from mixam_sdk.item_specification.models.item_specification import ItemSpecification
from mixam_sdk.item_specification.enums.component_type import ComponentType

if TYPE_CHECKING:  # avoid circular import at runtime
    from mixam_sdk.metadata.product.models.product_metadata import ProductMetadata

# Optional type for BC in __all__, real implementations live in models.validators
try:
    from mixam_sdk.metadata.product.models.validators import (
        ComponentValidator,
        DEFAULT_COMPONENT_VALIDATORS,
    )
except Exception:  # pragma: no cover
    ComponentValidator = object  # type: ignore
    DEFAULT_COMPONENT_VALIDATORS = {}  # type: ignore


class ProductItemSpecificationValidator:
    def __init__(self, component_validators: Dict[ComponentType, "ComponentValidator"] | None = None):
        self._validators = component_validators or getattr(
            __import__(
                "mixam_sdk.metadata.product.models.validators",
                fromlist=["DEFAULT_COMPONENT_VALIDATORS"],
            ),
            "DEFAULT_COMPONENT_VALIDATORS",
            {},
        )

    def validate(self, metadata: ProductMetadata, spec: ItemSpecification):
        return metadata.validate(spec)
