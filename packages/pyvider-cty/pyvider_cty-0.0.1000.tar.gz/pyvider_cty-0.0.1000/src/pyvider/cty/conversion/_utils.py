# src/pyvider/cty/conversion/_utils.py
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Any

from pyvider.cty.config.defaults import (
    ERR_CANNOT_INFER_FROM_CTY_TYPE,
    ERR_CANNOT_INFER_FROM_CTY_VALUE,
)

# pyvider-cty/src/pyvider/cty/conversion/_utils.py
"""Internal conversion utilities to avoid circular dependencies."""


def _attrs_to_dict_safe(inst: Any) -> dict[str, Any]:
    """
    Safely converts an attrs instance to a dict, raising TypeError for CTY
    framework types to prevent accidental misuse during type inference.
    """
    # Local imports to prevent circular dependencies at module load time.
    from pyvider.cty.types import CtyType
    from pyvider.cty.values import CtyValue

    if isinstance(inst, CtyType):
        error_message = ERR_CANNOT_INFER_FROM_CTY_TYPE.format(type_name=type(inst).__name__)
        raise TypeError(error_message)
    if isinstance(inst, CtyValue):
        error_message = ERR_CANNOT_INFER_FROM_CTY_VALUE.format(type_name=type(inst).__name__)
        raise TypeError(error_message)

    res = {}
    # Use getattr to safely access __attrs_attrs__ which may not exist.
    for a in getattr(type(inst), "__attrs_attrs__", []):
        res[a.name] = getattr(inst, a.name)
    return res


# 🐍⛓️↔️🪄
