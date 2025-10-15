# src/pyvider/cty/values/markers.py
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from decimal import Decimal

from attrs import define

# pyvider/cty/values/markers.py
"""
This module contains simple marker classes to break import cycles.
"""


class UnknownValue:
    """A base marker class for all unknown value types."""

    pass


class UnrefinedUnknownValue(UnknownValue):
    """A marker class for a simple, unrefined unknown value."""

    def __repr__(self) -> str:
        return "UNREFINED_UNKNOWN"


@define(frozen=True, slots=True, auto_attribs=True, match_args=True)
class RefinedUnknownValue(UnknownValue):
    """Represents an unknown value with additional constraints."""

    is_known_null: bool | None = None
    string_prefix: str | None = None
    number_lower_bound: tuple[Decimal, bool] | None = None
    number_upper_bound: tuple[Decimal, bool] | None = None
    collection_length_lower_bound: int | None = None
    collection_length_upper_bound: int | None = None


# This singleton represents an unknown value with no refinements.
UNREFINED_UNKNOWN = UnrefinedUnknownValue()

# 🐍⛓️💰🪄
