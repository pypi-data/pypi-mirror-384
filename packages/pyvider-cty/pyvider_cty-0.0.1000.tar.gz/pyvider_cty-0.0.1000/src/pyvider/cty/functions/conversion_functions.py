# src/pyvider/cty/functions/conversion_functions.py
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Any

from pyvider.cty import CtyBool, CtyNumber, CtyString, CtyValue
from pyvider.cty.exceptions import CtyFunctionError


def to_string(input_val: CtyValue[Any]) -> CtyValue[Any]:
    if input_val.is_null or input_val.is_unknown:
        return CtyValue.unknown(CtyString())
    if isinstance(input_val.type, CtyBool):
        return CtyString().validate("true" if input_val.value else "false")
    if isinstance(input_val.type, CtyNumber):
        return CtyString().validate(str(input_val.value))
    return CtyString().validate(str(input_val.value))


def to_number(input_val: CtyValue[Any]) -> CtyValue[Any]:
    if input_val.is_null or input_val.is_unknown:
        return CtyValue.unknown(CtyNumber())
    try:
        return CtyNumber().validate(input_val.value)
    except Exception as e:
        raise CtyFunctionError(f"tostring: cannot convert {input_val.type.ctype} to number") from e


def to_bool(input_val: CtyValue[Any]) -> CtyValue[Any]:
    if input_val.is_null or input_val.is_unknown:
        return CtyValue.unknown(CtyBool())
    try:
        return CtyBool().validate(input_val.value)
    except Exception as e:
        raise CtyFunctionError(f"tobool: cannot convert {input_val.type.ctype} to bool") from e


# 🐍⛓️🔣🪄
