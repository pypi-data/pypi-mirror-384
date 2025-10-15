# src/pyvider/cty/functions/structural_functions.py
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Any

from pyvider.cty import CtyValue
from pyvider.cty.exceptions import CtyFunctionError


def coalesce(*args: CtyValue[Any]) -> CtyValue[Any]:
    if not args:
        raise CtyFunctionError("coalesce must have at least one argument")

    for arg in args:
        if not arg.is_null and not arg.is_unknown:
            return arg

    return CtyValue.null(args[-1].type)


# 🐍⛓️🔣🪄
