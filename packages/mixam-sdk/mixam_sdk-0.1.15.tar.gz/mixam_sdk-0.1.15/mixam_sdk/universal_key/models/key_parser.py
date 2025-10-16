from __future__ import annotations

import re
from typing import Dict

from mixam_sdk.item_specification.enums.component_type import ComponentType
from mixam_sdk.item_specification.enums.product import Product
from mixam_sdk.item_specification.models.item_specification import ItemSpecification
from mixam_sdk.item_specification.models.value_based import for_value as value_based_for_value
from mixam_sdk.universal_key.models.key_builder import COPIES_DELIMITER
from mixam_sdk.universal_key.models.parser_support import ParserSupport


STANDARD_DELIMITER = "-"

# Validation Regex
VALIDATION_REGEX = re.compile(r"^\d+" + re.escape(COPIES_DELIMITER) + r"\d+(-[a-z]{2}\{([\d.]+[a-z+]+-?)*})+$")

# Component Segment Pattern
COMPONENT_PATTERN = re.compile(r"(-[a-z]{2}\{.*?})")

# Member Parsing Patterns
MEMBER_CODE_PATTERN = re.compile(r"^[\d.]+([a-z+]+)$")
MEMBER_VALUE_PATTERN = re.compile(r"^([\d.]+)[a-z+]+$")


class KeyParser(ParserSupport):
    def parse(self, key: str) -> ItemSpecification:
        if not VALIDATION_REGEX.match(key):
            raise ValueError(f"Invalid key: {key}")
        try:
            copies_part, rest = key.split(COPIES_DELIMITER, 1)
            item_spec = ItemSpecification()
            item_spec.copies = int(copies_part)

            # product is numeric id up to first '-'
            first_dash = rest.find(STANDARD_DELIMITER)
            if first_dash == -1:
                raise RuntimeError("No component segments present in key")
            product_id_str = rest[:first_dash]
            product_id = int(product_id_str)
            item_spec.product = value_based_for_value(product_id, Product)

            # parse components
            comps_str = rest[first_dash:]
            for match in COMPONENT_PATTERN.finditer(comps_str):
                segment = match.group(0)
                # e.g., -bd{...}
                type_code = segment[len(STANDARD_DELIMITER): segment.index("{")]
                member_segments = segment[segment.index("{") + 1: segment.index("}")]

                # split into tokens like ['5c', '4f', ...] but our builder made 'value''code' (e.g. '5c') -> need value and code
                tokens: Dict[str, str] = {}
                if member_segments:
                    for seg in member_segments.split(STANDARD_DELIMITER):
                        if not seg:
                            continue
                        m_code = MEMBER_CODE_PATTERN.match(seg)
                        m_val = MEMBER_VALUE_PATTERN.match(seg)
                        if not (m_code and m_val):
                            raise RuntimeError(f"Invalid member segment: {seg}")
                        code = m_code.group(1)
                        val = m_val.group(1)
                        tokens[code] = val

                component_type = ComponentType.for_code(type_code)
                comp_cls = component_type.get_component_class()
                component = self.assemble_member_tokens(tokens, comp_cls)
                item_spec.components.append(component)

            # sort components by ComponentType declaration order (ordinal-like)
            order = {ct: i for i, ct in enumerate(list(ComponentType))}
            item_spec.components.sort(key=lambda c: order.get(c.component_type, 9999))
            return item_spec
        except Exception as e:
            raise RuntimeError(f"Key failed to parse: {key}", e)
