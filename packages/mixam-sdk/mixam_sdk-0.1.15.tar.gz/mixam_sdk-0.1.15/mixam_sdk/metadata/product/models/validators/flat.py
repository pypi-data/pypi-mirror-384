from __future__ import annotations

from mixam_sdk.item_specification.models.flat_component import FlatComponent
from mixam_sdk.item_specification.models.item_specification import ItemSpecification
from mixam_sdk.metadata.product.enums.trilean import Trilean
from mixam_sdk.metadata.product.models.product_metadata import ProductMetadata
from mixam_sdk.metadata.product.services.validation_result import ValidationResult
from .base import DefaultComponentValidator


class FlatComponentValidator(DefaultComponentValidator):
    def validate(self, product_metadata: ProductMetadata, item_specification: ItemSpecification, flat_component: FlatComponent, result: ValidationResult, base_path: str) -> None:
        # Ensure correct component type
        if not isinstance(flat_component, FlatComponent):
            result.add_error(
                path=base_path,
                message="Invalid component type for FlatComponentValidator: expected FlatComponent",
                code="validator.component.type_mismatch",
                expected="FlatComponent",
            )
            return
        # Base validator handles substrate/lamination.
        super().validate(product_metadata, item_specification, flat_component, result, base_path)

        # Flat-specific: rounded corners rule based on product.rounded_corners (Trilean)
        try:
            setting = product_metadata.rounded_corners
            if setting == Trilean.REQUIRED:
                if not flat_component.round_corners:
                    result.add_error(
                        path=f"{base_path}.roundCorners",
                        message="This product requires rounded corners",
                        code="flat.rounded_corners.required",
                    )
            elif setting == Trilean.UNAVAILABLE:
                if flat_component.round_corners:
                    result.add_error(
                        path=f"{base_path}.roundCorners",
                        message="This product does not support rounded corners",
                        code="flat.rounded_corners.unavailable",
                    )
            # OPTIONAL/LBS_TEXT -> no additional validation
        except Exception:
            pass


__all__ = ["FlatComponentValidator"]
