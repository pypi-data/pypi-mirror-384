# src/pyvider/cty/types/capsule.py
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from collections.abc import Callable
import inspect
from typing import Any, ClassVar

from pyvider.cty.exceptions import CtyValidationError
from pyvider.cty.types.base import CtyType
from pyvider.cty.types.structural import CtyDynamic
from pyvider.cty.values import CtyValue

# pyvider/cty/types/capsule.py
"""
Defines the CtyCapsule type for encapsulating opaque Python objects
within the CTY type system.
"""


class CtyCapsule(CtyType[Any]):
    """
    Represents a capsule type in the Cty type system.
    Capsule types are opaque types that can be used to wrap arbitrary Python objects.
    """

    _type_order: ClassVar[int] = 8

    def __init__(self, capsule_name: str, py_type: type) -> None:
        super().__init__()
        self.name = capsule_name
        self._py_type = py_type

    @property
    def py_type(self) -> type:
        return self._py_type

    def validate(self, value: object) -> CtyValue[Any]:
        val_to_check: object | None
        original_marks: frozenset[Any] = frozenset()

        if isinstance(value, CtyValue):
            if value.is_null:
                return CtyValue.null(self)
            if value.is_unknown:
                return CtyValue.unknown(self)
            val_to_check = value.value
            original_marks = value.marks
        else:
            val_to_check = value

        if val_to_check is None:
            return CtyValue.null(self)

        if not isinstance(val_to_check, self._py_type):
            raise CtyValidationError(
                f"Value is not an instance of {self._py_type.__name__}. Got {type(val_to_check).__name__}."
            )
        return CtyValue(self, val_to_check, marks=original_marks)

    def equal(self, other: CtyType[Any]) -> bool:
        if not isinstance(other, CtyCapsule) or isinstance(other, CtyCapsuleWithOps):
            return False
        return self.name == other.name and self._py_type == other._py_type

    def usable_as(self, other: CtyType[Any]) -> bool:
        if isinstance(other, CtyDynamic):
            return True
        return self.equal(other)

    def _to_wire_json(self) -> Any:
        return None

    def __str__(self) -> str:
        return f"CtyCapsule({self.name})"

    def __repr__(self) -> str:
        return f"CtyCapsule({self.name}, {self._py_type.__name__})"

    def __hash__(self) -> int:
        return hash((self.name, self._py_type))


class CtyCapsuleWithOps(CtyCapsule):
    """
    A CtyCapsule that supports custom operations like equality, hashing, and conversion.
    """

    def __init__(
        self,
        capsule_name: str,
        py_type: type,
        *,
        equal_fn: Callable[[Any, Any], bool] | None = None,
        hash_fn: Callable[[Any], int] | None = None,
        convert_fn: Callable[[Any, CtyType[Any]], CtyValue[Any] | None] | None = None,
    ) -> None:
        """
        Initializes a CtyCapsule with custom operational functions.
        """
        super().__init__(capsule_name, py_type)
        self.equal_fn = equal_fn
        self.hash_fn = hash_fn
        self.convert_fn = convert_fn
        self._validate_ops_arity()

    def _validate_ops_arity(self) -> None:
        """Internal method to validate the arity of provided operational functions."""
        if self.equal_fn and len(inspect.signature(self.equal_fn).parameters) != 2:
            raise TypeError("`equal_fn` must be a callable that accepts 2 arguments")
        if self.hash_fn and len(inspect.signature(self.hash_fn).parameters) != 1:
            raise TypeError("`hash_fn` must be a callable that accepts 1 argument")
        if self.convert_fn and len(inspect.signature(self.convert_fn).parameters) != 2:
            raise TypeError("`convert_fn` must be a callable that accepts 2 arguments")

    def equal(self, other: CtyType[Any]) -> bool:
        if not isinstance(other, CtyCapsuleWithOps):
            return False
        return (
            self.name == other.name
            and self._py_type == other._py_type
            and self.equal_fn == other.equal_fn
            and self.hash_fn == other.hash_fn
            and self.convert_fn == other.convert_fn
        )

    def __repr__(self) -> str:
        return f"CtyCapsuleWithOps({self.name}, {self._py_type.__name__})"

    def __hash__(self) -> int:
        return hash((self.name, self._py_type, self.equal_fn, self.hash_fn, self.convert_fn))


# 🐍⛓️🧱🪄
