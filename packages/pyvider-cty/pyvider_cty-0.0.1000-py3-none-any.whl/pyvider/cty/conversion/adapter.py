# src/pyvider/cty/conversion/adapter.py
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from decimal import Decimal
from typing import Any

from pyvider.cty.types import (
    CtyDynamic,
    CtyList,
    CtyMap,
    CtyObject,
    CtySet,
    CtyTuple,
)

# Local imports to break the circular dependency cycle.
from pyvider.cty.values import CtyValue


def cty_to_native(value: CtyValue[Any] | Any) -> Any:  # noqa: C901
    """
    Converts a CtyValue to its raw Python representation using an iterative
    approach to avoid recursion limits. This is safe for deeply nested structures.
    """
    if not isinstance(value, CtyValue):
        return value

    if value.is_unknown:
        return None  # Gracefully handle unknown values by returning None.

    POST_PROCESS = object()
    work_stack: list[Any] = [value]
    results: dict[int, Any] = {}
    processing: set[int] = set()

    while work_stack:
        current_item = work_stack.pop()

        if current_item is POST_PROCESS:
            val_to_process = work_stack.pop()
            val_id = id(val_to_process)
            processing.remove(val_id)

            # Robustness check for malformed collection values
            if not hasattr(val_to_process.value, "__iter__"):
                if isinstance(val_to_process.type, CtyList | CtySet):
                    results[val_id] = []
                elif isinstance(val_to_process.type, CtyTuple):
                    results[val_id] = ()
                elif isinstance(val_to_process.type, CtyMap | CtyObject):
                    results[val_id] = {}
                continue

            if isinstance(val_to_process.type, CtyDynamic):
                inner_id = id(val_to_process.value)
                results[val_id] = results[inner_id]
            elif isinstance(val_to_process.type, CtyObject | CtyMap):
                results[val_id] = {k: results[id(v)] for k, v in val_to_process.value.items()}
            elif isinstance(val_to_process.type, CtyList):
                results[val_id] = [results[id(item)] for item in val_to_process.value]
            elif isinstance(val_to_process.type, CtySet):
                # Use _canonical_sort_key for consistent sorting of set elements
                results[val_id] = sorted(
                    [results[id(item)] for item in val_to_process.value],
                    key=lambda v: v._canonical_sort_key() if isinstance(v, CtyValue) else repr(v),
                )
            elif isinstance(val_to_process.type, CtyTuple):
                results[val_id] = tuple(results[id(item)] for item in val_to_process.value)
            continue

        if not isinstance(current_item, CtyValue):
            results[id(current_item)] = current_item
            continue

        if current_item.is_unknown:
            results[id(current_item)] = None
            continue
        if current_item.is_null:
            results[id(current_item)] = None
            continue

        item_id = id(current_item)
        if item_id in results or item_id in processing:
            continue

        if isinstance(
            current_item.type,
            CtyObject | CtyMap | CtyList | CtySet | CtyTuple | CtyDynamic,
        ):
            processing.add(item_id)
            work_stack.extend([current_item, POST_PROCESS])

            if isinstance(current_item.type, CtyDynamic):
                work_stack.append(current_item.value)
            elif hasattr(current_item.value, "__iter__"):  # Robustness check
                child_values = (
                    list(current_item.value.values())
                    if isinstance(current_item.value, dict)
                    else list(current_item.value)
                )
                work_stack.extend(reversed(child_values))
        else:
            inner_val = current_item.value
            if isinstance(inner_val, Decimal):
                exponent = inner_val.as_tuple().exponent
                if isinstance(exponent, int) and exponent >= 0:
                    results[item_id] = int(inner_val)
                else:
                    results[item_id] = float(inner_val)
            else:
                results[item_id] = inner_val

    return results.get(id(value))


# 🐍⛓️↔️🪄
