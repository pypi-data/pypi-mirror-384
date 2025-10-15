# src/pyvider/cty/types/collections/set.py
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from collections import OrderedDict
from typing import Any, ClassVar, Generic, TypeVar, final

from attrs import define, field

from pyvider.cty.exceptions import CtySetValidationError, CtyValidationError
from pyvider.cty.types.base import CtyType
from pyvider.cty.validation.recursion import with_recursion_detection
from pyvider.cty.values import CtyValue

T = TypeVar("T")


@final
@define(frozen=True, slots=True)
class CtySet(CtyType[tuple[T, ...]], Generic[T]):
    ctype: ClassVar[str] = "set"
    _type_order: ClassVar[int] = 4
    element_type: CtyType[T] = field(kw_only=True)

    def __attrs_post_init__(self) -> None:
        if not isinstance(self.element_type, CtyType):
            raise CtySetValidationError(f"Expected CtyType for element_type, got {type(self.element_type)}")

    @with_recursion_detection
    def validate(self, value: object) -> CtyValue[tuple[T, ...]]:
        if value is None:
            return CtyValue.null(self)
        if isinstance(value, CtyValue):
            if value.is_unknown:
                return CtyValue.unknown(self)
            if value.is_null:
                return CtyValue.null(self)
            if (
                isinstance(value.type, CtySet)
                and value.type.equal(self)
                and isinstance(value.value, frozenset)
            ):
                return value
            value = value.value

        if not isinstance(value, list | tuple | set | frozenset):
            raise CtySetValidationError(
                f"Expected a Python set, frozenset, list, or tuple, got {type(value).__name__}"
            )

        unique_items: OrderedDict[tuple[Any, ...], CtyValue[Any]] = OrderedDict()
        for raw_item in value:
            try:
                validated_item = self.element_type.validate(raw_item)
                key = validated_item._canonical_sort_key()
                unique_items[key] = validated_item
            except CtyValidationError as e:
                raise CtySetValidationError(e.message, value=raw_item) from e
            except Exception as e:
                raise CtySetValidationError(f"Failed to process element for set: {e}", value=raw_item) from e

        is_unknown = any(v.is_unknown for v in unique_items.values())
        return CtyValue(vtype=self, value=frozenset(unique_items.values()), is_unknown=is_unknown)

    def equal(self, other: CtyType[Any]) -> bool:
        if not isinstance(other, CtySet):
            return False
        return self.element_type.equal(other.element_type)

    def usable_as(self, other: CtyType[Any]) -> bool:
        from pyvider.cty.types.structural import CtyDynamic

        if isinstance(other, CtyDynamic):
            return True
        if not isinstance(other, CtySet):
            return False
        return self.element_type.usable_as(other.element_type)

    def _to_wire_json(self) -> Any:
        return [self.ctype, self.element_type._to_wire_json()]

    def __str__(self) -> str:
        return f"set({self.element_type})"


# 🐍⛓️🧱🪄
