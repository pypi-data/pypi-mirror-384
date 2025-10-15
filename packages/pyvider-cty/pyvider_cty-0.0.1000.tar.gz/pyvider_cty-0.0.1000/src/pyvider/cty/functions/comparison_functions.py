# src/pyvider/cty/functions/comparison_functions.py
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Any

from pyvider.cty import CtyBool, CtyNumber, CtyString, CtyValue
from pyvider.cty.config.defaults import (
    COMPARISON_OPS_MAP,
    ERR_ALL_ARGS_SAME_TYPE,
    ERR_CANNOT_COMPARE,
    ERR_MIN_ONE_ARG,
)
from pyvider.cty.exceptions import CtyFunctionError
from pyvider.cty.values.markers import RefinedUnknownValue


def equal(a: CtyValue[Any], b: CtyValue[Any]) -> CtyValue[Any]:
    if a.is_unknown or b.is_unknown:
        return CtyValue.unknown(CtyBool())
    return CtyBool().validate(a == b)


def not_equal(a: CtyValue[Any], b: CtyValue[Any]) -> CtyValue[Any]:
    if a.is_unknown or b.is_unknown:
        return CtyValue.unknown(CtyBool())
    return CtyBool().validate(a != b)


def _compare(a: CtyValue[Any], b: CtyValue[Any], op: str) -> CtyValue[Any]:  # noqa: C901
    if a.is_null or b.is_null:
        return CtyValue.unknown(CtyBool())

    # Handle refined unknown comparisons
    if a.is_unknown or b.is_unknown:
        ref_a = a.value if isinstance(a.value, RefinedUnknownValue) else None
        ref_b = b.value if isinstance(b.value, RefinedUnknownValue) else None

        # Case 1: One is known, one is refined unknown
        if a.is_unknown and not b.is_unknown and ref_a:
            b_val = b.value
            if ref_a.number_upper_bound:
                upper, inclusive = ref_a.number_upper_bound
                if b_val > upper or (b_val == upper and not inclusive):
                    if op in (">", ">="):
                        return CtyBool().validate(False)
                    if op in ("<", "<="):
                        return CtyBool().validate(True)
            if ref_a.number_lower_bound:
                lower, inclusive = ref_a.number_lower_bound
                if b_val < lower or (b_val == lower and not inclusive):
                    if op in ("<", "<="):
                        return CtyBool().validate(False)
                    if op in (">", ">="):
                        return CtyBool().validate(True)
        elif b.is_unknown and not a.is_unknown and ref_b:
            a_val = a.value
            if ref_b.number_upper_bound:
                upper, inclusive = ref_b.number_upper_bound
                if a_val > upper or (a_val == upper and not inclusive):
                    if op in ("<", "<="):
                        return CtyBool().validate(False)
                    if op in (">", ">="):
                        return CtyBool().validate(True)
            if ref_b.number_lower_bound:
                lower, inclusive = ref_b.number_lower_bound
                if a_val < lower or (a_val == lower and not inclusive):
                    if op in (">", ">="):
                        return CtyBool().validate(False)
                    if op in ("<", "<="):
                        return CtyBool().validate(True)
        # Case 2: Both are refined unknowns
        elif a.is_unknown and b.is_unknown and ref_a and ref_b:
            if ref_a.number_upper_bound and ref_b.number_lower_bound:
                a_upper, a_inc = ref_a.number_upper_bound
                b_lower, b_inc = ref_b.number_lower_bound
                if a_upper < b_lower or (a_upper == b_lower and not (a_inc and b_inc)):
                    if op in ("<", "<="):
                        return CtyBool().validate(True)
                    if op in (">", ">="):
                        return CtyBool().validate(False)
            if ref_a.number_lower_bound and ref_b.number_upper_bound:
                a_lower, a_inc = ref_a.number_lower_bound
                b_upper, b_inc = ref_b.number_upper_bound
                if a_lower > b_upper or (a_lower == b_upper and not (a_inc and b_inc)):
                    if op in (">", ">="):
                        return CtyBool().validate(True)
                    if op in ("<", "<="):
                        return CtyBool().validate(False)

        return CtyValue.unknown(CtyBool())

    # Handle known value comparisons
    if not isinstance(a.type, CtyNumber | CtyString) or not a.type.equal(b.type):
        error_message = ERR_CANNOT_COMPARE.format(type1=a.type.ctype, type2=b.type.ctype)
        raise CtyFunctionError(error_message)

    ops = COMPARISON_OPS_MAP
    return CtyBool().validate(ops[op](a.value, b.value))


def greater_than(a: CtyValue[Any], b: CtyValue[Any]) -> CtyValue[Any]:
    return _compare(a, b, ">")


def greater_than_or_equal_to(a: CtyValue[Any], b: CtyValue[Any]) -> CtyValue[Any]:
    return _compare(a, b, ">=")


def less_than(a: CtyValue[Any], b: CtyValue[Any]) -> CtyValue[Any]:
    return _compare(a, b, "<")


def less_than_or_equal_to(a: CtyValue[Any], b: CtyValue[Any]) -> CtyValue[Any]:
    return _compare(a, b, "<=")


def _partition_args(
    *args: CtyValue[Any],
) -> tuple[list[CtyValue[Any]], list[CtyValue[Any]]]:
    """Separate arguments into known and unknown values."""
    known_args, unknown_args = [], []
    for v in args:
        if v.is_unknown:
            unknown_args.append(v)
        elif not v.is_null:
            known_args.append(v)
    return known_args, unknown_args


def _validate_homogeneous_types(known_args: list[CtyValue[Any]], op: str) -> None:
    """Ensure all known arguments have compatible types."""
    if not known_args:
        return
    is_all_numbers = all(isinstance(v.type, CtyNumber) for v in known_args)
    is_all_strings = all(isinstance(v.type, CtyString) for v in known_args)
    if not (is_all_numbers or is_all_strings):
        error_message = ERR_ALL_ARGS_SAME_TYPE.format(op=op)
        raise CtyFunctionError(error_message)


def _find_extreme_value(known_args: list[CtyValue[Any]], op: str) -> CtyValue[Any] | None:
    """Find the extreme (min/max) value among known arguments."""
    if not known_args:
        return None
    ops = {"max": __builtins__["max"], "min": __builtins__["min"]}
    return ops[op](known_args, key=lambda v: v.value)


def _filter_dominated_unknowns(
    unknown_args: list[CtyValue[Any]], extreme_known: CtyValue[Any], op: str
) -> list[CtyValue[Any]]:
    """Remove unknown values that are definitely dominated by the extreme known value."""
    remaining_unknowns = []
    for unk in unknown_args:
        if isinstance(unk.value, RefinedUnknownValue):
            ref = unk.value
            if op == "max":
                if ref.number_upper_bound and (extreme_known.value >= ref.number_upper_bound[0]):
                    continue
            elif op == "min" and ref.number_lower_bound and (extreme_known.value <= ref.number_lower_bound[0]):
                continue
        remaining_unknowns.append(unk)
    return remaining_unknowns


def _multi_compare(*args: CtyValue[Any], op: str) -> CtyValue[Any]:
    if not args:
        error_message = ERR_MIN_ONE_ARG.format(op=op)
        raise CtyFunctionError(error_message)

    known_args, unknown_args = _partition_args(*args)

    if not known_args and not unknown_args:
        return CtyValue.null(args[0].type)

    _validate_homogeneous_types(known_args, op)
    extreme_known = _find_extreme_value(known_args, op)

    if extreme_known:
        unknown_args = _filter_dominated_unknowns(unknown_args, extreme_known, op)

    if not unknown_args:
        return extreme_known if extreme_known else CtyValue.null(args[0].type)
    if not known_args and len(unknown_args) == 1:
        return unknown_args[0]
    return CtyValue.unknown(args[0].type)


def max_fn(*args: CtyValue[Any]) -> CtyValue[Any]:
    return _multi_compare(*args, op="max")


def min_fn(*args: CtyValue[Any]) -> CtyValue[Any]:
    return _multi_compare(*args, op="min")


# 🐍⛓️🔣🪄
