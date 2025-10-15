# src/pyvider/cty/marks.py
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Any

from attrs import define, field


def _convert_details(value: Any) -> frozenset[Any] | None:
    """Converter to ensure the 'details' field is always hashable."""
    if value is None:
        return None
    if isinstance(value, dict):
        return frozenset(value.items())
    if isinstance(value, list | set | tuple):
        return frozenset(value)
    return frozenset([value])


@define(frozen=True, slots=True)
class CtyMark:
    """
    Represents a mark that can be applied to a cty.Value.
    The 'details' attribute is automatically converted to a hashable frozenset.
    """

    name: str = field()
    details: frozenset[Any] | None = field(default=None, converter=_convert_details)

    def __repr__(self) -> str:
        if self.details is not None:
            return f"CtyMark({self.name!r}, {dict(self.details)!r})"
        return f"CtyMark({self.name!r})"

    def __str__(self) -> str:
        return self.name


# 🐍⛓️🤔🪄
