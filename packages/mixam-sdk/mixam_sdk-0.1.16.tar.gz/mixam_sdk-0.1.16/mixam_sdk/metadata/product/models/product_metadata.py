from __future__ import annotations

from typing import Optional, Annotated

from pydantic import BaseModel, Field, ConfigDict

from mixam_sdk.item_specification.enums.orientation import Orientation
from mixam_sdk.item_specification.models.item_specification import ItemSpecification
from mixam_sdk.metadata.product.enums.santa_type import SantaType
from mixam_sdk.metadata.product.enums.trilean import Trilean
from mixam_sdk.metadata.product.services.validation_result import ValidationResult
from mixam_sdk.utils.enum_json import enum_by_name_or_value, enum_dump_name
from .bound_metadata import BoundMetadata
from .colours_metadata import ColoursMetadata
from .component_requirement import ComponentRequirement
from .copies_metadata import CopiesMetadata
from .custom_size_metadata import CustomSizeMetadata
from .flap_metadata import FlapMetadata
from .foiling_metadata import FoilingMetadata
from .framed_metadata import FramedMetadata
from .lamination_metadata import LaminationMetadata
from .pre_drilled_holes_metadata import PreDrilledHolesMetadata
from .publication_metadata import PublicationMetadata
from .shrink_wrap_metadata import ShrinkWrapMetadata
from .standard_size_metadata import StandardSizeMetadata
from .substrate_design_metadata import SubstrateDesignMetadata
from .substrate_type_metadata import SubstrateTypeMetadata


class ProductMetadata(BaseModel):

    def validate(self, spec: ItemSpecification) -> ValidationResult:
        """
        Validate the provided ItemSpecification against this product metadata.
        This mirrors previous ProductItemSpecificationValidator behavior so callers
        can simply call metadata.validate(spec).
        """
        # Import validators from new models.validators package if available; fall back to services for BC
        try:
            from mixam_sdk.metadata.product.models.validators import (
                ComponentValidator,
                DefaultComponentValidator,
                DEFAULT_COMPONENT_VALIDATORS,
            )
        except Exception:
            from mixam_sdk.metadata.product.models.validators import (
                ComponentValidator,  # type: ignore
                DefaultComponentValidator,  # type: ignore
                DEFAULT_COMPONENT_VALIDATORS,  # type: ignore
            )

        result = ValidationResult()

        # Copies validation (base)
        copies = spec.copies
        cm = self.copies_metadata
        if copies < cm.minimum_value or copies > cm.maximum_value:
            result.add_error(
                path="copies",
                message=f"Copies {copies} out of range [{cm.minimum_value}, {cm.maximum_value}]",
                code="copies.out_of_range",
                range_min=cm.minimum_value,
                range_max=cm.maximum_value,
            )
        else:
            step = cm.step_value
            if step > 0:
                # Use initial_value as the step baseline when available (typical: 100),
                # and always allow the exact minimum_value as a valid edge case.
                baseline = cm.initial_value if cm.initial_value is not None else 0
                aligned = ((copies - baseline) % step == 0) or (copies == cm.minimum_value)
                if not aligned:
                    result.add_error(
                        path="copies",
                        message=f"Copies {copies} does not align with step {step} from minimum {cm.minimum_value}.",
                        code="copies.step_mismatch",
                        range_min=cm.minimum_value,
                        range_max=cm.maximum_value,
                    )

        # Validate component type counts against requirements (top-level)
        try:
            from collections import Counter
            counts = Counter([c.component_type for c in spec.components])
            # Build dict of requirements for quick access
            req_by_type = {req.component_type: req for req in self.component_requirements}
            # Check all present components are allowed and within min/max
            for ctype, count in counts.items():
                req = req_by_type.get(ctype)
                if req is None:
                    result.add_error(
                        path="itemSpecification",
                        message=f"Component type {ctype.name.lower()} is not allowed",
                        code="component_type.not_allowed",
                        component_type=ctype.name,
                    )
                else:
                    if count < req.minimum_instances:
                        result.add_error(
                            path="itemSpecification",
                            message=f"A minimum of {req.minimum_instances} {ctype.name.lower()} component(s) is required",
                            code="component_type.min_instances",
                            minimum=req.minimum_instances,
                            component_type=ctype.name,
                        )
                    if count > req.maximum_instances:
                        result.add_error(
                            path="itemSpecification",
                            message=f"A maximum of {req.maximum_instances} {ctype.name.lower()} component(s) is allowed",
                            code="component_type.max_instances",
                            maximum=req.maximum_instances,
                            component_type=ctype.name,
                        )
            # Also ensure required component types exist when absent
            for req in self.component_requirements:
                count = counts.get(req.component_type, 0)
                if count < req.minimum_instances:
                    result.add_error(
                        path="itemSpecification",
                        message=f"A minimum of {req.minimum_instances} {req.component_type.name.lower()} component(s) is required",
                        code="component_type.min_instances",
                        minimum=req.minimum_instances,
                        component_type=req.component_type.name,
                    )
        except Exception:
            # Do not crash validation if component requirements are missing or malformed
            pass

        # Component validation using component-based validators
        default_validator = DefaultComponentValidator()
        validators = DEFAULT_COMPONENT_VALIDATORS.copy()
        # Determine primary component index
        try:
            primary = spec.get_primary_component()
            primary_index = spec.components.index(primary)
        except Exception:
            primary_index = 0 if spec.components else -1
        # Use PrimaryComponentValidator for the primary component
        try:
            from mixam_sdk.metadata.product.models.validators.primary import PrimaryComponentValidator
            primary_validator = PrimaryComponentValidator()
        except Exception:
            primary_validator = default_validator
        for idx, component in enumerate(spec.components):
            base_path = f"components[{component.component_type.name}]"
            if idx == primary_index:
                # Apply primary-component-only rules first
                primary_validator.validate(self, spec, component, result, base_path)
                # Then apply component-specific validator for additional rules (e.g., cover/envelope)
                specific = validators.get(component.component_type, default_validator)
                if specific is not primary_validator:
                    specific.validate(self, spec, component, result, base_path)
            else:
                # Non-primary components: apply their specific validator (which should run base checks via super())
                specific = validators.get(component.component_type, default_validator)
                specific.validate(self, spec, component, result, base_path)

        return result

    product_id: int = Field(
        alias="productId",
    )

    sub_product_id: int = Field(
        alias="subProductId",
    )

    santa_type: Annotated[SantaType, enum_by_name_or_value(SantaType), enum_dump_name] = Field(
        default=SantaType.QUOTE,
        alias="santaType",
    )

    product_name: str = Field(
        alias="productName",
    )

    copies_metadata: CopiesMetadata = Field(
        alias="copiesMetadata",
    )

    standard_sizes: list[StandardSizeMetadata] = Field(
        alias="standardSizes",
    )

    colours_metadata: ColoursMetadata = Field(
        alias="coloursMetadata",
    )

    lamination_metadata: LaminationMetadata | None = Field(
        default=None,
        alias="laminationMetadata",
    )

    substrate_types: list[SubstrateTypeMetadata] = Field(
        alias="substrateTypes",
    )

    envelope_substrate_types: list[SubstrateTypeMetadata] = Field(
        alias="envelopeSubstrateTypes",
    )

    cover_substrate_types: list[SubstrateTypeMetadata] = Field(
        alias="coverSubstrateTypes",
    )

    substrate_designs: list[SubstrateDesignMetadata] = Field(
        alias="substrateDesigns",
    )

    custom_size_metadata: Optional[CustomSizeMetadata] = Field(
        default=None,
        alias="customSizeMetadata",
    )

    default_orientation: Optional[Annotated[Orientation, enum_by_name_or_value(Orientation), enum_dump_name]] = Field(
        default=None,
        alias="defaultOrientation",
    )

    auto_orientable: bool = Field(
        default=False,
        alias="autoOrientable",
    )

    bound_metadata: Optional[BoundMetadata] = Field(
        default=None,
        alias="boundMetadata",
    )

    framed_metadata: Optional[FramedMetadata] = Field(
        default=None,
        alias="framedMetadata",
    )

    foiling_metadata: FoilingMetadata = Field(
        alias="foilingMetadata",
    )

    pre_drilled_holes_metadata: PreDrilledHolesMetadata = Field(
        alias="preDrilledHolesMetadata",
    )

    rounded_corners: Annotated[Trilean, enum_by_name_or_value(Trilean), enum_dump_name] = Field(
        default=Trilean.UNAVAILABLE,
        alias="roundedCorners",
    )

    shrink_wrap_metadata: ShrinkWrapMetadata = Field(
        alias="shrinkWrapMetadata",
    )

    publication_metadata: PublicationMetadata = Field(
        alias="publicationMetadata",
    )

    initial_specification: ItemSpecification | None = Field(
        default=None,
        alias="initialSpecification",
    )

    flap_metadata: Optional[FlapMetadata] = Field(
        default=None,
        alias="flapMetadata",
    )

    component_requirements: list[ComponentRequirement] = Field(
        alias="componentRequirements",
    )

    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore",
        frozen=True,
        strict=True,
        validate_assignment=True,
    )


__all__ = ["ProductMetadata"]
