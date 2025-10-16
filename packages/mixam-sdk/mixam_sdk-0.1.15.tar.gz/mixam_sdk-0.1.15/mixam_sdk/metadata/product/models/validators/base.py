from __future__ import annotations

from typing import Protocol

from mixam_sdk.item_specification.interfaces.component_protocol import TwoSidedComponent as ITwoSidedComponent
from mixam_sdk.item_specification.models.component_support import ComponentSupport
from mixam_sdk.item_specification.models.item_specification import ItemSpecification
from mixam_sdk.metadata.product.models.product_metadata import ProductMetadata
from mixam_sdk.metadata.product.services.validation_result import ValidationResult


class ComponentValidator(Protocol):
    def validate(self, product_metadata: ProductMetadata, item_specification: ItemSpecification, component: ComponentSupport, result: ValidationResult, base_path: str) -> None: ...


class DefaultComponentValidator:
    """
    Applies standard validations common to all components. More specific validators
    can subclass this and extend/override validate.
    """

    def validate(self, product_metadata: ProductMetadata, item_specification: ItemSpecification, component: ComponentSupport, result: ValidationResult, base_path: str) -> None:
        # Standard size / format vs available metadata sizes
        try:
            allowed_formats = {s.format for s in product_metadata.standard_sizes}
            if component.format not in allowed_formats:
                result.add_error(
                    path=f"{base_path}.format",
                    message=f"Format '{component.format}' not available for this product.",
                    code="size.format.unavailable",
                    allowed=sorted(list(allowed_formats)),
                )
        except Exception:
            pass

        # Substrate design if present
        try:
            if component.substrate.design is not None:
                allowed_designs = {sd.substrate_design.name for sd in product_metadata.substrate_designs}
                if allowed_designs and component.substrate.design.name not in allowed_designs:
                    result.add_error(
                        path=f"{base_path}.substrate.design",
                        message=f"Substrate design '{component.substrate.design.name}' not available for this product.",
                        code="substrate.design.unavailable",
                        allowed=sorted(list(allowed_designs)),
                    )
        except Exception:
            pass


__all__ = [
    "ComponentValidator",
    "DefaultComponentValidator",
]
