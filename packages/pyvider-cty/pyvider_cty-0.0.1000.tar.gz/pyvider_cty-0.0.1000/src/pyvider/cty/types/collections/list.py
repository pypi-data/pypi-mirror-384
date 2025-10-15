# src/pyvider/cty/types/collections/list.py
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, ClassVar, Generic, TypeVar, final

from attrs import define, field
from provide.foundation.errors import error_boundary

from pyvider.cty.exceptions import CtyListValidationError, CtyValidationError
from pyvider.cty.path import CtyPath, IndexStep
from pyvider.cty.types.base import CtyType
from pyvider.cty.types.structural import CtyDynamic
from pyvider.cty.validation.recursion import with_recursion_detection
from pyvider.cty.values import CtyValue

if TYPE_CHECKING:
    pass

T = TypeVar("T")


@final
@define(frozen=True, slots=True)
class CtyList(CtyType[tuple[T, ...]], Generic[T]):
    ctype: ClassVar[str] = "list"
    _type_order: ClassVar[int] = 5
    element_type: CtyType[T] = field(kw_only=True)

    def __attrs_post_init__(self) -> None:
        if not isinstance(self.element_type, CtyType):
            raise CtyListValidationError(
                f"Expected CtyType for element_type, got {type(self.element_type).__name__}"
            )

    @with_recursion_detection
    def validate(self, value: object) -> CtyValue[tuple[T, ...]]:  # noqa: C901
        from pyvider.cty.values import CtyValue

        if isinstance(value, CtyValue):
            if self.equal(value.type) and isinstance(value.value, tuple):
                return value  # Fast path for already-validated values
            if value.is_null:
                return CtyValue.null(self)
            if value.is_unknown:
                return CtyValue.unknown(self)
            value = value.value

        if value is None:
            return CtyValue.null(self)

        raw_list_to_validate: Sequence[object] | None = None

        if isinstance(value, list | tuple | set | frozenset):
            raw_list_to_validate = list(value)
        else:
            raise CtyListValidationError(f"Expected list, tuple, or CtyValue list, got {type(value).__name__}")

        if not isinstance(raw_list_to_validate, list | tuple):
            raise CtyListValidationError(
                f"Value to validate is not a list or tuple, but {type(raw_list_to_validate).__name__}"
            )

        validated_elements: list[CtyValue[T]] = []
        for i, item in enumerate(raw_list_to_validate):
            with error_boundary(
                context={
                    "operation": "list_element_validation",
                    "list_index": i,
                    "element_type": str(self.element_type),
                    "item_type": type(item).__name__,
                }
            ):
                if item is None and not isinstance(self.element_type, CtyDynamic):
                    raise CtyListValidationError(
                        f"List elements cannot be null for element type {self.element_type.ctype}",
                        path=CtyPath(steps=[IndexStep(i)]),
                    )
                try:
                    validated_item = self.element_type.validate(item)
                    validated_elements.append(validated_item)
                except CtyValidationError as e:
                    new_path = CtyPath(steps=[IndexStep(i)] + (e.path.steps if e.path else []))
                    raise CtyListValidationError(
                        e.message, value=item, path=new_path, original_exception=e
                    ) from e

        is_unknown = any(v.is_unknown for v in validated_elements)
        return CtyValue(vtype=self, value=tuple(validated_elements), is_unknown=is_unknown)

    def element_at(self, container: object, index: int) -> CtyValue[T]:
        from pyvider.cty.values import CtyValue

        if isinstance(container, CtyValue):
            if not isinstance(container.type, CtyList):
                raise CtyListValidationError(
                    f"Expected CtyValue with CtyList type, got CtyValue with {type(container.type).__name__}"
                )
            if container.is_null:
                raise IndexError(f"Cannot access element at index {index} in a null list.")
            if container.is_unknown:
                return CtyValue.unknown(self.element_type)
            if not isinstance(container.value, list | tuple):
                raise CtyListValidationError(
                    f"Internal error: CtyValue of CtyList type does not wrap a list/tuple, got {type(container.value).__name__}"
                )
            try:
                return self.element_type.validate(container.value[index])
            except TypeError as e:
                raise TypeError(f"list indices must be integers or slices, not {type(index).__name__}") from e

        raise CtyListValidationError(f"Expected CtyValue[CtyList], got {type(container).__name__}")

    def equal(self, other: CtyType[Any]) -> bool:
        if not isinstance(other, CtyList):
            return False
        return self.element_type.equal(other.element_type)

    def usable_as(self, other: CtyType[Any]) -> bool:
        from pyvider.cty.types.structural import CtyDynamic

        if isinstance(other, CtyDynamic):
            return True
        if not isinstance(other, CtyList):
            return False
        return self.element_type.usable_as(other.element_type)

    def _to_wire_json(self) -> Any:
        return [self.ctype, self.element_type._to_wire_json()]

    def __str__(self) -> str:
        return f"list({self.element_type})"

    def __repr__(self) -> str:
        return f"CtyList(element_type={self.element_type!r})"


# 🐍⛓️🧱🪄
