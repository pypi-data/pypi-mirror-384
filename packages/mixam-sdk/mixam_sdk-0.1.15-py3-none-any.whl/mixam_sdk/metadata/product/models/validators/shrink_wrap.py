from __future__ import annotations

from mixam_sdk.item_specification.models.item_specification import ItemSpecification
from mixam_sdk.item_specification.models.shrink_wrap_component import ShrinkWrapComponent
from mixam_sdk.metadata.product.models.product_metadata import ProductMetadata
from mixam_sdk.metadata.product.services.validation_result import ValidationResult
from .base import DefaultComponentValidator


class ShrinkWrapComponentValidator(DefaultComponentValidator):
    def validate(self, product_metadata: ProductMetadata, item_specification: ItemSpecification, shrink_wrap_component: ShrinkWrapComponent, result: ValidationResult, base_path: str) -> None:
        # Ensure correct component type
        if not isinstance(shrink_wrap_component, ShrinkWrapComponent):
            result.add_error(
                path=base_path,
                message="Invalid component type for ShrinkWrapComponentValidator: expected ShrinkWrapComponent",
                code="validator.component.type_mismatch",
                expected="ShrinkWrapComponent",
            )
            return
        super().validate(product_metadata, item_specification, shrink_wrap_component, result, base_path)


__all__ = ["ShrinkWrapComponentValidator"]
