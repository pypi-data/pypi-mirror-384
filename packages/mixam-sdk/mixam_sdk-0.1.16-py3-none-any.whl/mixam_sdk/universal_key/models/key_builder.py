from __future__ import annotations

from typing import List

from mixam_sdk.item_specification.enums.component_type import ComponentType
from mixam_sdk.item_specification.interfaces.component_protocol import component_comparator_key
from mixam_sdk.item_specification.models.item_specification import ItemSpecification
from mixam_sdk.universal_key.models.builder_support import BuilderSupport


COPIES_DELIMITER = "~"


class KeyBuilder(BuilderSupport):
    def build(self, item_spec: ItemSpecification) -> str:
        components: List[str] = []
        comps = sorted(item_spec.components, key=component_comparator_key)
        for comp in comps:
            tokens = self.collect_member_tokens(comp)
            rendered = "-".join([f"{v}{k}" for k, v in tokens.items()])
            code = comp.component_type.get_code()
            components.append(f"-{code}{{{rendered}}}")

        components_str = "".join(components)
        product = item_spec.product
        product_value = getattr(product, "value", None)
        if product_value is None or isinstance(product_value, str):
            product_value = product.name

        return f"{item_spec.copies}{COPIES_DELIMITER}{product_value}{components_str}"
