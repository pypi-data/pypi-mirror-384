# src/pyvider/cty/functions/numeric_functions.py
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from decimal import Decimal, InvalidOperation
import math
from typing import Any

from pyvider.cty import CtyNumber, CtyString, CtyValue
from pyvider.cty.config.defaults import POSITIVE_BOUNDARY, ZERO_VALUE
from pyvider.cty.exceptions import CtyFunctionError
from pyvider.cty.values.markers import RefinedUnknownValue


def _get_refined_components(
    a: CtyValue[Any], b: CtyValue[Any]
) -> tuple[RefinedUnknownValue, RefinedUnknownValue, Any, Any]:
    """Extract refinement components from two values."""
    ref_a = a.value if isinstance(a.value, RefinedUnknownValue) else RefinedUnknownValue()
    ref_b = b.value if isinstance(b.value, RefinedUnknownValue) else RefinedUnknownValue()
    val_a = a.value if not a.is_unknown else None
    val_b = b.value if not b.is_unknown else None
    return ref_a, ref_b, val_a, val_b


def _propagate_add_refinements(
    ref_a: RefinedUnknownValue, ref_b: RefinedUnknownValue, val_a: Any, val_b: Any
) -> dict[str, Any]:
    """Handle refinement propagation for addition."""
    new_ref: dict[str, Any] = {}
    if val_a is not None:  # a is known, b is refined/unrefined
        if ref_b.number_lower_bound:
            new_ref["number_lower_bound"] = (
                val_a + ref_b.number_lower_bound[0],
                ref_b.number_lower_bound[1],
            )
        if ref_b.number_upper_bound:
            new_ref["number_upper_bound"] = (
                val_a + ref_b.number_upper_bound[0],
                ref_b.number_upper_bound[1],
            )
    elif val_b is not None:  # b is known, a is refined/unrefined
        if ref_a.number_lower_bound:
            new_ref["number_lower_bound"] = (
                ref_a.number_lower_bound[0] + val_b,
                ref_a.number_lower_bound[1],
            )
        if ref_a.number_upper_bound:
            new_ref["number_upper_bound"] = (
                ref_a.number_upper_bound[0] + val_b,
                ref_a.number_upper_bound[1],
            )
    else:  # both are refined/unrefined
        if ref_a.number_lower_bound and ref_b.number_lower_bound:
            new_ref["number_lower_bound"] = (
                ref_a.number_lower_bound[0] + ref_b.number_lower_bound[0],
                ref_a.number_lower_bound[1] and ref_b.number_lower_bound[1],
            )
        if ref_a.number_upper_bound and ref_b.number_upper_bound:
            new_ref["number_upper_bound"] = (
                ref_a.number_upper_bound[0] + ref_b.number_upper_bound[0],
                ref_a.number_upper_bound[1] and ref_b.number_upper_bound[1],
            )
    return new_ref


def _propagate_subtract_refinements(
    ref_a: RefinedUnknownValue, ref_b: RefinedUnknownValue, val_a: Any, val_b: Any
) -> dict[str, Any]:
    """Handle refinement propagation for subtraction."""
    new_ref: dict[str, Any] = {}
    if val_b is not None:
        if ref_a.number_lower_bound:
            new_ref["number_lower_bound"] = (
                ref_a.number_lower_bound[0] - val_b,
                ref_a.number_lower_bound[1],
            )
        if ref_a.number_upper_bound:
            new_ref["number_upper_bound"] = (
                ref_a.number_upper_bound[0] - val_b,
                ref_a.number_upper_bound[1],
            )
    elif val_a is not None:
        if ref_b.number_upper_bound:
            new_ref["number_lower_bound"] = (
                val_a - ref_b.number_upper_bound[0],
                ref_b.number_upper_bound[1],
            )
        if ref_b.number_lower_bound:
            new_ref["number_upper_bound"] = (
                val_a - ref_b.number_lower_bound[0],
                ref_b.number_lower_bound[1],
            )
    else:
        if ref_a.number_lower_bound and ref_b.number_upper_bound:
            new_ref["number_lower_bound"] = (
                ref_a.number_lower_bound[0] - ref_b.number_upper_bound[0],
                ref_a.number_lower_bound[1] and ref_b.number_upper_bound[1],
            )
        if ref_a.number_upper_bound and ref_b.number_lower_bound:
            new_ref["number_upper_bound"] = (
                ref_a.number_upper_bound[0] - ref_b.number_lower_bound[0],
                ref_a.number_upper_bound[1] and ref_b.number_lower_bound[1],
            )
    return new_ref


def _propagate_multiply_refinements(
    ref_a: RefinedUnknownValue, ref_b: RefinedUnknownValue, val_a: Any, val_b: Any
) -> dict[str, Any]:
    """Handle refinement propagation for multiplication."""
    new_ref: dict[str, Any] = {}
    known_val, unknown_ref = (val_a, ref_b) if val_a is not None else (val_b, ref_a)
    if known_val is not None:
        if known_val > POSITIVE_BOUNDARY:
            if unknown_ref.number_lower_bound:
                new_ref["number_lower_bound"] = (
                    unknown_ref.number_lower_bound[0] * known_val,
                    unknown_ref.number_lower_bound[1],
                )
            if unknown_ref.number_upper_bound:
                new_ref["number_upper_bound"] = (
                    unknown_ref.number_upper_bound[0] * known_val,
                    unknown_ref.number_upper_bound[1],
                )
        elif known_val < POSITIVE_BOUNDARY:
            if unknown_ref.number_upper_bound:
                new_ref["number_lower_bound"] = (
                    unknown_ref.number_upper_bound[0] * known_val,
                    unknown_ref.number_upper_bound[1],
                )
            if unknown_ref.number_lower_bound:
                new_ref["number_upper_bound"] = (
                    unknown_ref.number_lower_bound[0] * known_val,
                    unknown_ref.number_lower_bound[1],
                )
    return new_ref


def _propagate_divide_refinements(ref_a: RefinedUnknownValue, val_b: Any) -> dict[str, Any]:
    """Handle refinement propagation for division."""
    new_ref: dict[str, Any] = {}
    if val_b is not None:
        if val_b > POSITIVE_BOUNDARY:
            if ref_a.number_lower_bound:
                new_ref["number_lower_bound"] = (
                    ref_a.number_lower_bound[0] / val_b,
                    ref_a.number_lower_bound[1],
                )
            if ref_a.number_upper_bound:
                new_ref["number_upper_bound"] = (
                    ref_a.number_upper_bound[0] / val_b,
                    ref_a.number_upper_bound[1],
                )
        elif val_b < POSITIVE_BOUNDARY:
            if ref_a.number_upper_bound:
                new_ref["number_lower_bound"] = (
                    ref_a.number_upper_bound[0] / val_b,
                    ref_a.number_upper_bound[1],
                )
            if ref_a.number_lower_bound:
                new_ref["number_upper_bound"] = (
                    ref_a.number_lower_bound[0] / val_b,
                    ref_a.number_lower_bound[1],
                )
    return new_ref


def _propagate_refined_unknowns(op: str, a: CtyValue[Any], b: CtyValue[Any]) -> CtyValue[Any]:
    """Helper to propagate refinements for binary numeric operations."""
    if not (isinstance(a.value, RefinedUnknownValue) or isinstance(b.value, RefinedUnknownValue)):
        return CtyValue.unknown(CtyNumber())

    ref_a, ref_b, val_a, val_b = _get_refined_components(a, b)

    if op == "add":
        new_ref = _propagate_add_refinements(ref_a, ref_b, val_a, val_b)
    elif op == "subtract":
        new_ref = _propagate_subtract_refinements(ref_a, ref_b, val_a, val_b)
    elif op == "multiply":
        new_ref = _propagate_multiply_refinements(ref_a, ref_b, val_a, val_b)
    elif op == "divide":
        new_ref = _propagate_divide_refinements(ref_a, val_b)
    else:
        new_ref = {}

    return CtyValue.unknown(CtyNumber(), value=RefinedUnknownValue(**new_ref))


def add(a: CtyValue[Any], b: CtyValue[Any]) -> CtyValue[Any]:
    if not isinstance(a.type, CtyNumber) or not isinstance(b.type, CtyNumber):
        raise CtyFunctionError("add: arguments must be numbers")
    if a.is_null or b.is_null:
        return CtyValue.unknown(CtyNumber())
    if a.is_unknown or b.is_unknown:
        return _propagate_refined_unknowns("add", a, b)
    return CtyNumber().validate(a.value + b.value)


def subtract(a: CtyValue[Any], b: CtyValue[Any]) -> CtyValue[Any]:
    if not isinstance(a.type, CtyNumber) or not isinstance(b.type, CtyNumber):
        raise CtyFunctionError("subtract: arguments must be numbers")
    if a.is_null or b.is_null:
        return CtyValue.unknown(CtyNumber())
    if a.is_unknown or b.is_unknown:
        return _propagate_refined_unknowns("subtract", a, b)
    return CtyNumber().validate(a.value - b.value)


def multiply(a: CtyValue[Any], b: CtyValue[Any]) -> CtyValue[Any]:
    if not isinstance(a.type, CtyNumber) or not isinstance(b.type, CtyNumber):
        raise CtyFunctionError("multiply: arguments must be numbers")
    if a.is_null or b.is_null:
        return CtyValue.unknown(CtyNumber())
    if (not a.is_unknown and a.value == ZERO_VALUE) or (not b.is_unknown and b.value == ZERO_VALUE):
        return CtyNumber().validate(ZERO_VALUE)
    if a.is_unknown or b.is_unknown:
        return _propagate_refined_unknowns("multiply", a, b)
    return CtyNumber().validate(a.value * b.value)


def divide(a: CtyValue[Any], b: CtyValue[Any]) -> CtyValue[Any]:
    if not isinstance(a.type, CtyNumber) or not isinstance(b.type, CtyNumber):
        raise CtyFunctionError("divide: arguments must be numbers")
    if a.is_null or b.is_null:
        return CtyValue.unknown(CtyNumber())
    if not b.is_unknown and b.value == ZERO_VALUE:
        raise CtyFunctionError("divide by zero")
    if a.is_unknown or b.is_unknown:
        return _propagate_refined_unknowns("divide", a, b)
    return CtyNumber().validate(a.value / b.value)


def modulo(a: CtyValue[Any], b: CtyValue[Any]) -> CtyValue[Any]:
    if not isinstance(a.type, CtyNumber) or not isinstance(b.type, CtyNumber):
        raise CtyFunctionError("modulo: arguments must be numbers")
    if a.is_null or a.is_unknown or b.is_null or b.is_unknown:
        return CtyValue.unknown(CtyNumber())
    if b.value == ZERO_VALUE:
        raise CtyFunctionError("modulo by zero")
    return CtyNumber().validate(math.fmod(a.value, b.value))


def negate(a: CtyValue[Any]) -> CtyValue[Any]:
    if not isinstance(a.type, CtyNumber):
        raise CtyFunctionError("negate: argument must be a number")
    if a.is_null:
        return CtyValue.null(CtyNumber())
    if a.is_unknown:
        if isinstance(a.value, RefinedUnknownValue):
            ref = a.value
            new_ref = {}
            if ref.number_upper_bound:
                new_ref["number_lower_bound"] = (
                    -ref.number_upper_bound[0],
                    ref.number_upper_bound[1],
                )
            if ref.number_lower_bound:
                new_ref["number_upper_bound"] = (
                    -ref.number_lower_bound[0],
                    ref.number_lower_bound[1],
                )
            return (
                CtyValue.unknown(CtyNumber(), value=RefinedUnknownValue(**new_ref))
                if new_ref
                else CtyValue.unknown(CtyNumber())
            )
        return CtyValue.unknown(CtyNumber())
    return CtyNumber().validate(-a.value)


def abs_fn(input_val: CtyValue[Any]) -> CtyValue[Any]:
    if not isinstance(input_val.type, CtyNumber):
        raise CtyFunctionError(f"abs: input must be a number, got {input_val.type.ctype}")
    if input_val.is_null:
        return CtyValue.null(CtyNumber())
    if input_val.is_unknown:
        if isinstance(input_val.value, RefinedUnknownValue):
            ref = input_val.value
            new_ref = {}
            lower, upper = ref.number_lower_bound, ref.number_upper_bound
            if lower and upper:
                l_val, l_inc = lower
                u_val, u_inc = upper
                if l_val >= 0:
                    return input_val
                if u_val <= 0:
                    new_ref["number_lower_bound"] = (-u_val, u_inc)
                    new_ref["number_upper_bound"] = (-l_val, l_inc)
                else:
                    new_ref["number_lower_bound"] = (Decimal(0), True)
                    new_upper_val = max(abs(l_val), abs(u_val))
                    new_upper_inc = l_inc if abs(l_val) >= abs(u_val) else u_inc
                    new_ref["number_upper_bound"] = (new_upper_val, new_upper_inc)
            elif lower and lower[0] >= 0:
                return input_val
            elif upper and upper[0] <= 0:
                new_ref["number_lower_bound"] = (-upper[0], upper[1])
            return (
                CtyValue.unknown(CtyNumber(), value=RefinedUnknownValue(**new_ref))
                if new_ref
                else CtyValue.unknown(CtyNumber())
            )
        return CtyValue.unknown(CtyNumber())
    return CtyNumber().validate(abs(input_val.value))


def ceil_fn(input_val: CtyValue[Any]) -> CtyValue[Any]:
    if not isinstance(input_val.type, CtyNumber):
        raise CtyFunctionError(f"ceil: input must be a number, got {input_val.type.ctype}")
    if input_val.is_null or input_val.is_unknown:
        return input_val
    return CtyNumber().validate(Decimal(math.ceil(input_val.value)))


def floor_fn(input_val: CtyValue[Any]) -> CtyValue[Any]:
    if not isinstance(input_val.type, CtyNumber):
        raise CtyFunctionError(f"floor: input must be a number, got {input_val.type.ctype}")
    if input_val.is_null or input_val.is_unknown:
        return input_val
    return CtyNumber().validate(Decimal(math.floor(input_val.value)))


def log_fn(num_val: CtyValue[Any], base_val: CtyValue[Any]) -> CtyValue[Any]:
    if not isinstance(num_val.type, CtyNumber) or not isinstance(base_val.type, CtyNumber):
        raise CtyFunctionError("log: arguments must be numbers")
    if num_val.is_null or num_val.is_unknown or base_val.is_null or base_val.is_unknown:
        return CtyValue.unknown(CtyNumber())
    num, base = num_val.value, base_val.value
    if num <= 0:
        raise CtyFunctionError(f"log: number must be positive, got {num}")
    if base <= 0:
        raise CtyFunctionError(f"log: base must be positive, got {base}")
    if base == 1:
        raise CtyFunctionError("log: base cannot be 1")
    try:
        result = Decimal(str(math.log(float(num), float(base))))
        return CtyNumber().validate(result)
    except ValueError as e:
        raise CtyFunctionError(f"log: math domain error: {e}") from e


def pow_fn(num_val: CtyValue[Any], power_val: CtyValue[Any]) -> CtyValue[Any]:
    if not isinstance(num_val.type, CtyNumber) or not isinstance(power_val.type, CtyNumber):
        raise CtyFunctionError("pow: arguments must be numbers")
    if num_val.is_null or num_val.is_unknown or power_val.is_null or power_val.is_unknown:
        return CtyValue.unknown(CtyNumber())
    try:
        result = num_val.value**power_val.value
        return CtyNumber().validate(result)
    except InvalidOperation as e:
        raise CtyFunctionError(f"pow: invalid operation: {e}") from e


def signum_fn(input_val: CtyValue[Any]) -> CtyValue[Any]:
    if not isinstance(input_val.type, CtyNumber):
        raise CtyFunctionError(f"signum: input must be a number, got {input_val.type.ctype}")
    if input_val.is_null or input_val.is_unknown:
        return input_val
    val = input_val.value
    if val < 0:
        return CtyNumber().validate(Decimal("-1"))
    if val > 0:
        return CtyNumber().validate(Decimal("1"))
    return CtyNumber().validate(Decimal("0"))


def parseint_fn(str_val: CtyValue[Any], base_val: CtyValue[Any]) -> CtyValue[Any]:
    if not isinstance(str_val.type, CtyString) or not isinstance(base_val.type, CtyNumber):
        raise CtyFunctionError("parseint: arguments must be string and number")
    if str_val.is_null or base_val.is_null:
        return CtyValue.null(CtyNumber())
    if str_val.is_unknown or base_val.is_unknown:
        return CtyValue.unknown(CtyNumber())
    s, base = str_val.value, int(base_val.value)
    if not (base == 0 or 2 <= base <= 36):
        raise CtyFunctionError(f"parseint: base must be 0 or between 2 and 36, got {base}")
    try:
        parsed_int = int(s, base)
        return CtyNumber().validate(Decimal(parsed_int))
    except (ValueError, TypeError):
        return CtyValue.null(CtyNumber())


def int_fn(val: CtyValue[Any]) -> CtyValue[Any]:
    if not isinstance(val.type, CtyNumber):
        raise CtyFunctionError(f"int: argument must be a number, got {val.type.ctype}")
    if val.is_null or val.is_unknown:
        return val
    return CtyNumber().validate(Decimal(int(val.value)))


# 🐍⛓️🔣🪄
