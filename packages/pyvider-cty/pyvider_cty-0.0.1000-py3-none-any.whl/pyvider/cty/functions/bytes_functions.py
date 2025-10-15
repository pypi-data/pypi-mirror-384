# src/pyvider/cty/functions/bytes_functions.py
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Any

from pyvider.cty import CtyNumber, CtyValue
from pyvider.cty.config.defaults import (
    ERR_BYTESLEN_ARG_MUST_BE_BYTES_CAPSULE,
    ERR_BYTESSLICE_ARGS_MUST_BE_BYTES_NUMBER_NUMBER,
)
from pyvider.cty.exceptions import CtyFunctionError
from pyvider.cty.types import BytesCapsule


def byteslen(buffer: CtyValue[Any]) -> CtyValue[Any]:
    if not buffer.type.equal(BytesCapsule):
        error_message = ERR_BYTESLEN_ARG_MUST_BE_BYTES_CAPSULE.format(type=buffer.type.ctype)
        raise CtyFunctionError(error_message)
    if buffer.is_unknown or buffer.is_null:
        return CtyValue.unknown(CtyNumber())
    return CtyNumber().validate(len(buffer.value))  # type: ignore[arg-type]


def bytesslice(buffer: CtyValue[Any], start: CtyValue[Any], end: CtyValue[Any]) -> CtyValue[Any]:
    if (
        not buffer.type.equal(BytesCapsule)
        or not isinstance(start.type, CtyNumber)
        or not isinstance(end.type, CtyNumber)
    ):
        error_message = ERR_BYTESSLICE_ARGS_MUST_BE_BYTES_NUMBER_NUMBER
        raise CtyFunctionError(error_message)
    if (
        buffer.is_unknown
        or buffer.is_null
        or start.is_unknown
        or start.is_null
        or end.is_unknown
        or end.is_null
    ):
        return CtyValue.unknown(BytesCapsule)

    start_idx, end_idx = int(start.value), int(end.value)  # type: ignore[call-overload]
    return BytesCapsule.validate(buffer.value[start_idx:end_idx])  # type: ignore[index]


# 🐍⛓️🔣🪄
