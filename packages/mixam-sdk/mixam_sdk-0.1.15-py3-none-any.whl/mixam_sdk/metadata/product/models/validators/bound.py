from __future__ import annotations

from mixam_sdk.item_specification.enums.binding_edge import BindingEdge
from mixam_sdk.item_specification.enums.binding_loops import BindingLoops
from mixam_sdk.item_specification.enums.component_type import ComponentType
from mixam_sdk.item_specification.enums.lamination import Lamination
from mixam_sdk.item_specification.enums.product import Product as ProductEnum
from mixam_sdk.item_specification.models.bound_component import BoundComponent
from mixam_sdk.item_specification.models.item_specification import ItemSpecification
from mixam_sdk.metadata.product.models.page_count_metadata import PageCountMetadata
from mixam_sdk.metadata.product.models.product_metadata import ProductMetadata
from mixam_sdk.metadata.product.services.validation_result import ValidationResult
from .base import DefaultComponentValidator
from .utils import select_binding_type_option_for_item_specification


class BoundComponentValidator(DefaultComponentValidator):
    def validate(self, product_metadata: ProductMetadata, item_specification: ItemSpecification, bound_component: BoundComponent, result: ValidationResult, base_path: str) -> None:
        # Ensure correct component type
        if not isinstance(bound_component, BoundComponent):
            result.add_error(
                path=base_path,
                message="Invalid component type for BoundComponentValidator: expected BoundComponent",
                code="validator.component.type_mismatch",
                expected="BoundComponent",
            )
            return
        # Base validator handles substrate/lamination; run it first.
        super().validate(product_metadata, item_specification, bound_component, result, base_path)

        # Bound-specific checks
        try:



            bound_metadata = product_metadata.bound_metadata
            if bound_metadata is None:
                result.add_error(
                    path=f"{base_path}",
                    message="Bound metadata is missing; cannot validate bound component",
                    code="bound.metadata.missing",
                )
                return

            # Loops must be TWO_LOOPS
            if bound_component.binding.loops != BindingLoops.TWO_LOOPS:
                result.add_error(
                    path=f"{base_path}.binding.loops",
                    message="Only TWO_LOOPS is supported",
                    code="bound.binding.loops.unsupported",
                )

            # Ribbon colour must be among metadata if selected
            if bound_component.ribbon_colour.name != "NONE":
                allowed_ribbons = {rm.ribbon_colour.name for rm in bound_metadata.ribbon_metadata}
                if allowed_ribbons and bound_component.ribbon_colour.name not in allowed_ribbons:
                    result.add_error(
                        path=f"{base_path}.ribbonColour",
                        message="Unsupported Ribbon Colour.",
                        code="bound.ribbon_colour.unavailable",
                        allowed=sorted(list(allowed_ribbons)),
                    )

            # Head & Tail Bands validation when selected
            if bound_component.binding.head_and_tail_bands.name != "NONE":
                allowed_hnt = {m.head_and_tail_bands.name for m in bound_metadata.head_and_tail_band_metadata}
                if allowed_hnt and bound_component.binding.head_and_tail_bands.name not in allowed_hnt:
                    result.add_error(
                        path=f"{base_path}.binding.headAndTailBands",
                        message="Unsupported Head & Tail Band.",
                        code="bound.head_and_tail_bands.unavailable",
                        allowed=sorted(list(allowed_hnt)),
                    )

            # Pages increment/default exceptions
            if bound_metadata.pages_increment > 0 and item_specification is not None:
                if bound_component.pages % bound_metadata.pages_increment != 0:
                    if item_specification.product in {ProductEnum.VR_DESK_CALENDARS, ProductEnum.VR_WALL_CALENDARS}:
                        if bound_component.pages != bound_metadata.default_pages:
                            result.add_error(
                                path=f"{base_path}.pages",
                                message=f"Pages must be {bound_metadata.default_pages}",
                                code="bound.pages.must_equal_default",
                                allowed=[bound_metadata.default_pages],
                            )
                    else:
                        result.add_error(
                            path=f"{base_path}.pages",
                            message=f"Pages must be an increment of {bound_metadata.pages_increment}",
                            code="bound.pages.increment",
                        )

            # Determine binding type option to drive further rules (if we have the spec)
            binding_type_option = None
            if item_specification is not None:
                match = select_binding_type_option_for_item_specification(item_specification, product_metadata.cover_substrate_types, bound_metadata)
                if match.binding_type_option is None and match.errors:
                    # Return at least one helpful violation
                    for v in match.errors:
                        result.add_error(v.path, v.message, v.code, **getattr(v, "extra", {}))
                binding_type_option = match.binding_type_option

            # Page count ranges
            if item_specification is not None:
                # Find body substrate weight metadata to inspect page counts
                substrate_type_metadata = next((t for t in product_metadata.substrate_types if t.id == bound_component.substrate.type_id), None)
                substrate_colour_metadata = next((c for c in (substrate_type_metadata.substrate_colours if substrate_type_metadata else []) if c.id == bound_component.substrate.colour_id), None)
                substrate_weight_metadata = next((w for w in (substrate_colour_metadata.weights if substrate_colour_metadata else []) if w.id == bound_component.substrate.weight_id), None)
                page_count_md: PageCountMetadata | None = None
                if substrate_weight_metadata is not None and binding_type_option is not None:
                    page_count_md = next((pc for pc in substrate_weight_metadata.page_counts if pc.binding_type == binding_type_option.binding_type), None)
                if page_count_md is not None:
                    if not (page_count_md.min <= bound_component.pages <= page_count_md.max):
                        result.add_error(
                            path=f"{base_path}.pages",
                            message=f"Pages must be between {page_count_md.min} and {page_count_md.max} [Page Range]",
                            code="bound.pages.range.binding_type",
                            range_min=page_count_md.min,
                            range_max=page_count_md.max,
                        )
                else:
                    # Fallback to global min/max
                    global_min_pages = bound_metadata.global_min_pages or 0
                    from mixam_sdk.metadata.product.models.bound_metadata import BoundMetadata as _BM
                    global_max_pages = bound_metadata.global_max_pages or _BM.DEFAULT_GLOBAL_MAX_PAGES
                    if not (global_min_pages <= bound_component.pages <= global_max_pages):
                        result.add_error(
                            path=f"{base_path}.pages",
                            message=f"Pages must be between {global_min_pages} and {global_max_pages} [Global]",
                            code="bound.pages.range.global",
                            range_min=global_min_pages,
                            range_max=global_max_pages,
                        )

            # Hard rule: minimum 8 pages unless a cover component exists
            if item_specification is not None and bound_component.pages < 8 and not item_specification.has_component(ComponentType.COVER):
                result.add_error(
                    path=f"{base_path}.pages",
                    message="Minimum pages is 8 for bound items without a cover component",
                    code="bound.pages.min_without_cover",
                )

            # Binding Edge rules
            if not bound_metadata.binding_edge_options and bound_component.binding.edge != BindingEdge.LEFT_RIGHT:
                result.add_error(
                    path=f"{base_path}.binding.edge",
                    message="Only LEFT_RIGHT binding edge is supported by this product",
                    code="bound.binding.edge.only_left_right",
                )
            elif bound_metadata.binding_edge_options:
                allowed_edges = {e.binding_edge.name for e in bound_metadata.binding_edge_options}
                if bound_component.binding.edge.name not in allowed_edges:
                    result.add_error(
                        path=f"{base_path}.binding.edge",
                        message="Unsupported Binding Edge.",
                        code="bound.binding.edge.unavailable",
                        allowed=sorted(list(allowed_edges)),
                    )

            # Body lamination options (Layflats support lamination on body)
            lam_meta = product_metadata.lamination_metadata
            front_opts = lam_meta.front_options if lam_meta is not None else []
            if not front_opts and bound_component.lamination != Lamination.NONE:
                result.add_error(
                    path=f"{base_path}.lamination",
                    message="Lamination is not supported by this product",
                    code="bound.lamination.unsupported",
                )
            elif bound_component.lamination != Lamination.NONE:
                allowed_values = {int(opt.value) for opt in front_opts}
                if allowed_values and bound_component.lamination.get_value() not in allowed_values and bound_component.lamination.value not in allowed_values:
                    result.add_error(
                        path=f"{base_path}.lamination",
                        message="Unsupported lamination. This product accepts configured front laminations",
                        code="bound.lamination.option_invalid",
                        allowed=sorted(list(allowed_values)),
                    )

        except Exception:
            # Ignore metadata issues
            pass


__all__ = ["BoundComponentValidator"]
