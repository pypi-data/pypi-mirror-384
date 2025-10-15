# src/pyvider/cty/conversion/type_encoder.py
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

# pyvider-cty/src/pyvider/cty/conversion/type_encoder.py
from typing import Any

from pyvider.cty.config.defaults import ERR_EXPECTED_CTYTYPE
from pyvider.cty.types import CtyType


def encode_cty_type_to_wire_json(cty_type: CtyType[Any]) -> Any:
    """
    Encodes a CtyType into a JSON-serializable structure for the wire format
    by delegating to the type's own `_to_wire_json` method.
    """
    if not isinstance(cty_type, CtyType):
        error_message = ERR_EXPECTED_CTYTYPE.format(type_name=type(cty_type).__name__)
        raise TypeError(error_message)
    return cty_type._to_wire_json()


# 🐍⛓️↔️🪄
