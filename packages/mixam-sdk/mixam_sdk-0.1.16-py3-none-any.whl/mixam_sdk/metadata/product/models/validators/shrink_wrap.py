from __future__ import annotations

from mixam_sdk.item_specification.models.item_specification import ItemSpecification
from mixam_sdk.item_specification.models.shrink_wrap_component import ShrinkWrapComponent
from mixam_sdk.metadata.product.models.product_metadata import ProductMetadata
from mixam_sdk.metadata.product.services.validation_result import ValidationResult
from .base import DefaultComponentValidator


class ShrinkWrapComponentValidator(DefaultComponentValidator):
    def validate(self, product_metadata: ProductMetadata, item_specification: ItemSpecification, shrink_wrap_component: ShrinkWrapComponent, result: ValidationResult, base_path: str) -> None:

        if not isinstance(shrink_wrap_component, ShrinkWrapComponent):
            result.add_error(
                path=base_path,
                message="Invalid component type for ShrinkWrapComponentValidator: expected ShrinkWrapComponent",
                code="validator.component.type_mismatch",
                expected="ShrinkWrapComponent",
            )
            return

        super().validate(product_metadata, item_specification, shrink_wrap_component, result, base_path)

        # Shrink wrap specific validations
        try:
            options = product_metadata.shrink_wrap_metadata.options
        except Exception:
            options = []

        # If there are no available shrink wrap options, having this component is invalid
        if not options:
            result.add_error(
                path=base_path,
                message="Shrink wrap is not available for this product",
                code="shrink_wrap.unavailable",
            )
            return

        # Find a matching shrink wrap option by substrate type/weight
        try:
            st_id = shrink_wrap_component.substrate.type_id
            sw_id = shrink_wrap_component.substrate.weight_id
            match = next((o for o in options if o.substrate_type_id == st_id and o.substrate_weight_id == sw_id), None)
        except Exception:
            match = None

        if match is None:
            try:
                allowed = sorted({(o.substrate_type_id, o.substrate_weight_id) for o in options})
            except Exception:
                allowed = []
            result.add_error(
                path=f"{base_path}.substrate",
                message="Shrink wrap option not available for selected substrate",
                code="shrink_wrap.option.unavailable",
                allowed=allowed,
            )
            return

        # Validate bundle size against the selected option's rules
        try:
            bundle_size = int(shrink_wrap_component.bundle_size)
            min_size = int(match.bundle_minimum)
            increment = int(match.bundle_increment)
        except Exception:
            return

        if bundle_size < min_size:
            result.add_error(
                path=f"{base_path}.bundleSize",
                message=f"Bundle size must be at least {min_size}",
                code="shrink_wrap.bundle_size.minimum",
                minimum=min_size,
            )
            return

        if increment > 0 and bundle_size % increment != 0:
            result.add_error(
                path=f"{base_path}.bundleSize",
                message=f"Bundle size must increase in increments of {increment} starting from {min_size}",
                code="shrink_wrap.bundle_size.increment",
                minimum=min_size,
                increment=increment,
            )


__all__ = ["ShrinkWrapComponentValidator"]
