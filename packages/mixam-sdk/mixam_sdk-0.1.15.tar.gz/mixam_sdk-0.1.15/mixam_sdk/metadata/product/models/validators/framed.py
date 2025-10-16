from __future__ import annotations

from mixam_sdk.item_specification.models.framed_component import FramedComponent
from mixam_sdk.item_specification.models.item_specification import ItemSpecification
from mixam_sdk.metadata.product.models.product_metadata import ProductMetadata
from mixam_sdk.metadata.product.services.validation_result import ValidationResult
from .base import DefaultComponentValidator


class FramedComponentValidator(DefaultComponentValidator):
    def validate(self, product_metadata: ProductMetadata, item_specification: ItemSpecification, framed_component: FramedComponent, result: ValidationResult, base_path: str) -> None:
        # Ensure correct component type
        if not isinstance(framed_component, FramedComponent):
            result.add_error(
                path=base_path,
                message="Invalid component type for FramedComponentValidator: expected FramedComponent",
                code="validator.component.type_mismatch",
                expected="FramedComponent",
            )
            return
        # Run generic/base validations first
        super().validate(product_metadata, item_specification, framed_component, result, base_path)

        # Component-specific: frame depth option must be supported by product.framed_metadata
        try:
            framed_metadata = product_metadata.framed_metadata
            if framed_metadata is None:
                # Missing framed metadata -> treat as error
                result.add_error(
                    path=f"{base_path}.frameDepth",
                    message="Framed metadata is missing; cannot validate frame depth for this product.",
                    code="framed.metadata.missing",
                )
                return
            frame_depth_options = framed_metadata.frame_depth_options or []
            allowed = {opt.frame_depth.name for opt in frame_depth_options}
            if allowed and framed_component.frame_depth.name not in allowed:
                result.add_error(
                    path=f"{base_path}.frameDepth",
                    message="Unsupported frame depth. This product accepts the configured frame depths",
                    code="framed.frame_depth.unavailable",
                    allowed=sorted(list(allowed)),
                )
        except Exception:
            # Ignore metadata issues
            pass


__all__ = ["FramedComponentValidator"]
