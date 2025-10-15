# src/pyvider/cty/types/structural/tuple.py
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import builtins
from typing import Any, ClassVar

from attrs import define, field

from pyvider.cty.exceptions import (
    CtyTupleValidationError,
    CtyTypeMismatchError,
    CtyValidationError,
)
from pyvider.cty.path import CtyPath, IndexStep
from pyvider.cty.types.base import CtyType
from pyvider.cty.validation.recursion import with_recursion_detection
from pyvider.cty.values import CtyValue


@define(frozen=True, slots=True)
class CtyTuple(CtyType[tuple[object, ...]]):
    ctype: ClassVar[str] = "tuple"
    _type_order: ClassVar[int] = 3
    element_types: tuple[CtyType[Any], ...] = field()

    @element_types.validator
    def _validate_element_types(self, attribute: str, value: tuple[CtyType[Any], ...]) -> None:
        if not isinstance(value, tuple):
            raise CtyTupleValidationError(f"element_types must be a tuple, got {type(value).__name__}")
        for i, typ in enumerate(value):
            if not isinstance(typ, CtyType):
                raise CtyTupleValidationError(
                    f"Element type at index {i} must be a CtyType, got {type(typ).__name__}"
                )

    @with_recursion_detection
    def validate(self, value: object) -> CtyValue[tuple[Any, ...]]:
        if isinstance(value, CtyValue):
            if isinstance(value.type, CtyTuple) and value.type.equal(self) and isinstance(value.value, tuple):
                return value
            if value.is_unknown:
                return CtyValue.unknown(self)
            if value.is_null:
                return CtyValue.null(self)
            value = value.value
        if not isinstance(value, list | tuple):
            raise CtyTupleValidationError(f"Expected tuple or list, got {type(value).__name__}")
        if len(value) != len(self.element_types):
            raise CtyTupleValidationError(f"Expected {len(self.element_types)} elements, got {len(value)}")

        validated_elements = []
        for i, (raw_element, element_type) in enumerate(zip(value, self.element_types, strict=False)):
            try:
                validated_element = element_type.validate(raw_element)
                validated_elements.append(validated_element)
            except CtyValidationError as e:
                new_path = CtyPath(steps=[IndexStep(i)] + (e.path.steps if e.path else []))
                raise CtyTupleValidationError(
                    e.message, value=raw_element, path=new_path, original_exception=e
                ) from e

        is_unknown = any(v.is_unknown for v in validated_elements)
        return CtyValue(self, tuple(validated_elements), is_unknown=is_unknown)

    def element_at(self, container_value: CtyValue[Any], index: int | builtins.slice) -> CtyValue[Any]:
        if not isinstance(index, int | slice):
            raise TypeError(f"Tuple indices must be integers or slices, not {type(index).__name__}")
        if isinstance(index, slice):
            if container_value.is_null or container_value.is_unknown:
                sliced_types = self.element_types[index]
                new_tuple_type = CtyTuple(element_types=sliced_types)
                return (
                    CtyValue.null(new_tuple_type)
                    if container_value.is_null
                    else CtyValue.unknown(new_tuple_type)
                )
            if not isinstance(container_value.value, tuple):
                raise CtyTupleValidationError(
                    "Internal tuple value is inconsistent with type definition for slicing."
                )
            sliced_values = container_value.value[index]
            sliced_types = self.element_types[index]
            new_tuple_type = CtyTuple(element_types=sliced_types)
            return CtyValue(vtype=new_tuple_type, value=sliced_values)
        effective_index = index
        num_elements = len(self.element_types)
        if effective_index < 0:
            effective_index += num_elements
        if not (0 <= effective_index < num_elements):
            raise IndexError("tuple index out of range")
        if container_value.is_null or container_value.is_unknown:
            element_type_at_index = self.element_types[effective_index]
            return (
                CtyValue.null(element_type_at_index)
                if container_value.is_null
                else CtyValue.unknown(element_type_at_index)
            )
        if not isinstance(container_value.value, tuple) or len(container_value.value) != num_elements:
            raise CtyTupleValidationError("Internal tuple value is inconsistent with type definition.")
        return self.element_types[effective_index].validate(container_value.value[effective_index])

    def equal(self, other: CtyType[Any]) -> bool:
        if not isinstance(other, CtyTuple):
            return False
        if len(self.element_types) != len(other.element_types):
            return False
        return all(t1.equal(t2) for t1, t2 in zip(self.element_types, other.element_types, strict=False))

    def usable_as(self, other: CtyType[Any]) -> bool:
        from pyvider.cty.types.structural import CtyDynamic

        if isinstance(other, CtyDynamic):
            return True
        if not isinstance(other, CtyTuple):
            return False
        if len(self.element_types) != len(other.element_types):
            return False
        return all(t1.usable_as(t2) for t1, t2 in zip(self.element_types, other.element_types, strict=False))

    def _to_wire_json(self) -> Any:
        elems_json = [elem_type._to_wire_json() for elem_type in self.element_types]
        return [self.ctype, elems_json]

    def __getitem__(self, index: int | builtins.slice) -> CtyType[Any] | CtyTuple | tuple[CtyType[Any], ...]:
        return self.element_types[index]

    def __str__(self) -> str:
        if not self.element_types:
            return "tuple([])"
        elements = ", ".join(str(vtype) for vtype in self.element_types)
        return f"tuple([{elements}])"

    def slice(
        self,
        container_value: CtyValue[Any],
        start: int,
        end: int | None = None,
        step: int | None = None,
    ) -> CtyValue[Any]:
        if not isinstance(container_value, CtyValue) or not container_value.type.equal(self):
            raise CtyTypeMismatchError(
                f"Container value must be a CtyValue of type {self}, got {container_value}"
            )
        slice_obj = slice(start, end, step)
        return self.element_at(container_value, slice_obj)


# 🐍⛓️🧱🪄
