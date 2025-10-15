# src/pyvider/cty/types/primitives/number.py
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import TYPE_CHECKING, Any, ClassVar

from attrs import define

from pyvider.cty.exceptions import CtyNumberValidationError
from pyvider.cty.types.base import CtyType

if TYPE_CHECKING:
    from pyvider.cty.values import CtyValue


@define(frozen=True, slots=True)
class CtyNumber(CtyType[Decimal]):
    ctype: ClassVar[str] = "number"
    _type_order: ClassVar[int] = 0

    def validate(self, value: object) -> CtyValue[Decimal]:
        from pyvider.cty.values import CtyValue, UnknownValue

        if isinstance(value, UnknownValue):
            return CtyValue.unknown(self)

        if isinstance(value, CtyValue):
            if value.is_null:
                return CtyValue.null(self)
            if value.is_unknown:
                return CtyValue.unknown(self)
            raw_value = value.value
        else:
            raw_value = value

        if raw_value is None:
            return CtyValue.null(self)

        if isinstance(raw_value, bool):
            raw_value = 1 if raw_value else 0

        if isinstance(raw_value, bytes):
            raw_value = raw_value.decode("utf-8")

        try:
            return CtyValue(vtype=self, value=Decimal(raw_value))  # type: ignore
        except (TypeError, ValueError, InvalidOperation) as e:
            raise CtyNumberValidationError(
                f"Cannot represent {type(raw_value).__name__} value '{raw_value}' as Decimal"
            ) from e

    def equal(self, other: CtyType[Any]) -> bool:
        return isinstance(other, CtyNumber)

    def usable_as(self, other: CtyType[Any]) -> bool:
        from pyvider.cty.types.structural import CtyDynamic

        return isinstance(other, CtyNumber | CtyDynamic)

    def _to_wire_json(self) -> Any:
        return self.ctype

    def __str__(self) -> str:
        return "number"

    def is_primitive_type(self) -> bool:
        return True


# 🐍⛓️🧱🪄
