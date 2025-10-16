from __future__ import annotations

from mixam_sdk.item_specification.models.item_specification import ItemSpecification
from mixam_sdk.item_specification.models.sample_pack_component import SamplePackComponent
from mixam_sdk.metadata.product.models.product_metadata import ProductMetadata
from mixam_sdk.metadata.product.services.validation_result import ValidationResult
from .base import DefaultComponentValidator


class SamplePackComponentValidator(DefaultComponentValidator):
    def validate(self, product_metadata: ProductMetadata, item_specification: ItemSpecification, sample_pack_component: SamplePackComponent, result: ValidationResult, base_path: str) -> None:
        # Ensure correct component type
        if not isinstance(sample_pack_component, SamplePackComponent):
            result.add_error(
                path=base_path,
                message="Invalid component type for SamplePackComponentValidator: expected SamplePackComponent",
                code="validator.component.type_mismatch",
                expected="SamplePackComponent",
            )
            return
        # Sample Pack specific rules are not modeled; apply only base validations
        super().validate(product_metadata, item_specification, sample_pack_component, result, base_path)


__all__ = ["SamplePackComponentValidator"]
