# src/pyvider/cty/parser.py
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Any

from provide.foundation.errors import error_boundary

from pyvider.cty.config.defaults import (
    TYPE_KIND_LIST,
    TYPE_KIND_MAP,
    TYPE_KIND_SET,
)
from pyvider.cty.exceptions import CtyValidationError
from pyvider.cty.types import (
    CtyBool,
    CtyDynamic,
    CtyList,
    CtyMap,
    CtyNumber,
    CtyObject,
    CtySet,
    CtyString,
    CtyTuple,
    CtyType,
)

# pyvider-cty/src/pyvider/cty/parser.py
"""
Contains logic for parsing Terraform's JSON-based type constraint strings
into the framework's internal CtyType objects.
"""


def parse_tf_type_to_ctytype(tf_type: Any) -> CtyType[Any]:  # noqa: C901
    """
    Parses a Terraform type constraint, represented as a raw Python object
    (typically from JSON), into a CtyType instance.
    """
    with error_boundary(
        context={
            "operation": "terraform_type_parsing",
            "tf_type": str(tf_type),
            "tf_type_python_type": type(tf_type).__name__,
        }
    ):
        if isinstance(tf_type, str):
            match tf_type:
                case "string":
                    return CtyString()
                case "number":
                    return CtyNumber()
                case "bool":
                    return CtyBool()
                case "dynamic":
                    return CtyDynamic()
                case _:
                    raise CtyValidationError(f"Unknown primitive type name: '{tf_type}'")

        if isinstance(tf_type, list) and len(tf_type) == 2:
            type_kind, type_spec = tf_type

            # Handle collection types where the spec is a single type
            if type_kind in (TYPE_KIND_LIST, TYPE_KIND_SET, TYPE_KIND_MAP):
                element_type = parse_tf_type_to_ctytype(type_spec)
                match type_kind:
                    case "list":
                        return CtyList(element_type=element_type)
                    case "set":
                        return CtySet(element_type=element_type)
                    case "map":
                        return CtyMap(element_type=element_type)

            # Handle structural types where the spec is a container
            match type_kind:
                case "object":
                    if not isinstance(type_spec, dict):
                        raise CtyValidationError(
                            f"Object type spec must be a dictionary, got {type(type_spec).__name__}"
                        )
                    attr_types = {name: parse_tf_type_to_ctytype(spec) for name, spec in type_spec.items()}
                    return CtyObject(attribute_types=attr_types)
                case "tuple":
                    if not isinstance(type_spec, list):
                        raise CtyValidationError(
                            f"Tuple type spec must be a list, got {type(type_spec).__name__}"
                        )
                    elem_types = tuple(parse_tf_type_to_ctytype(spec) for spec in type_spec)
                    return CtyTuple(element_types=elem_types)

        raise CtyValidationError(f"Invalid Terraform type specification: {tf_type}")


# Alias for backward compatibility if needed, though direct use is preferred.
parse_type_string_to_ctytype = parse_tf_type_to_ctytype

# 🐍⛓️🤔🪄
