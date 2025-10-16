from __future__ import annotations

from mixam_sdk.item_specification.enums.orientation import Orientation
from mixam_sdk.item_specification.models.folded_component import FoldedComponent
from mixam_sdk.item_specification.models.item_specification import ItemSpecification
from mixam_sdk.metadata.product.models.product_metadata import ProductMetadata
from mixam_sdk.metadata.product.services.validation_result import ValidationResult
from .base import DefaultComponentValidator


class FoldedComponentValidator(DefaultComponentValidator):
    def validate(self, product_metadata: ProductMetadata, item_specification: ItemSpecification, folded_component: FoldedComponent, result: ValidationResult, base_path: str) -> None:
        # Ensure correct component type
        if not isinstance(folded_component, FoldedComponent):
            result.add_error(
                path=base_path,
                message="Invalid component type for FoldedComponentValidator: expected FoldedComponent",
                code="validator.component.type_mismatch",
                expected="FoldedComponent",
            )
            return
        # Generic checks first
        super().validate(product_metadata, item_specification, folded_component, result, base_path)

        try:

            # Find matching StandardSize metadata by format and standard size
            standard_size_metadata = next(
                (
                    s for s in product_metadata.standard_sizes
                    if s.format == folded_component.format and s.standard_size == folded_component.standard_size
                ),
                None,
            )
            if standard_size_metadata is None or standard_size_metadata.folding_options is None:
                result.add_error(
                    path=f"{base_path}.standardSize",
                    message="Unsupported format & standard size combination for folding",
                    code="folded.standard_size.combo.invalid",
                )
                return

            folding_options = standard_size_metadata.folding_options

            # Select options based on orientation
            if folded_component.orientation == Orientation.PORTRAIT:
                options = folding_options.portrait_options
                orient_key = "portrait"
            else:
                options = folding_options.landscape_options
                orient_key = "landscape"

            # Validate simple fold is allowed in this orientation
            allowed_folds = {opt.simple_fold.name for opt in options}
            if allowed_folds and folded_component.simple_fold.name not in allowed_folds:
                result.add_error(
                    path=f"{base_path}.simpleFold",
                    message="Unsupported simple fold for this size & orientation",
                    code="folded.simple_fold.unavailable",
                    allowed=sorted(list(allowed_folds)),
                    orientation=orient_key,
                )
                return

            # Validate sides allowed for the selected simple fold
            selected = next((opt for opt in options if opt.simple_fold == folded_component.simple_fold), None)
            if selected is None:
                # Defensive: if not found due to data mismatch, already handled above
                return
            if selected.available_sides and folded_component.sides not in selected.available_sides:
                result.add_error(
                    path=f"{base_path}.sides",
                    message="Unsupported number of sides for this size & orientation",
                    code="folded.sides.unavailable",
                    allowed=sorted(list(selected.available_sides)),
                    orientation=orient_key,
                )
        except Exception:
            # Ignore metadata issues
            pass


__all__ = ["FoldedComponentValidator"]
