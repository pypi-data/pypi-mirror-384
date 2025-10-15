# src/pyvider/cty/__init__.py
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from pyvider.cty._version import __version__
from pyvider.cty.conversion import convert, unify
from pyvider.cty.exceptions import (
    CtyAttributeValidationError,
    CtyConversionError,
    CtyListValidationError,
    CtyMapValidationError,
    CtySetValidationError,
    CtyTupleValidationError,
    CtyTypeMismatchError,
    CtyTypeParseError,
    CtyValidationError,
)
from pyvider.cty.marks import CtyMark
from pyvider.cty.parser import parse_tf_type_to_ctytype, parse_type_string_to_ctytype
from pyvider.cty.types import (
    BytesCapsule,
    CtyBool,
    CtyCapsule,
    CtyCapsuleWithOps,
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
from pyvider.cty.values import CtyValue

"""
The pyvider.cty package is a pure-Python implementation of the concepts
from HashiCorp's `cty` library, providing a rich type system for the framework.
"""

__all__ = [
    "BytesCapsule",
    "CtyAttributeValidationError",
    "CtyBool",
    "CtyCapsule",
    "CtyCapsuleWithOps",
    "CtyConversionError",
    "CtyDynamic",
    "CtyList",
    "CtyListValidationError",
    "CtyMap",
    "CtyMapValidationError",
    "CtyMark",
    "CtyNumber",
    "CtyObject",
    "CtySet",
    "CtySetValidationError",
    "CtyString",
    "CtyTuple",
    "CtyTupleValidationError",
    "CtyType",
    "CtyTypeMismatchError",
    "CtyTypeParseError",
    "CtyValidationError",
    "CtyValue",
    "__version__",
    "convert",
    "parse_tf_type_to_ctytype",
    "parse_type_string_to_ctytype",
    "unify",
]

# 🐍⛓️🤔🪄
