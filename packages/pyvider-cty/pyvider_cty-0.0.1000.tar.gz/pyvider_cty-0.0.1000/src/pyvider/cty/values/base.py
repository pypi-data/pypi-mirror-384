# src/pyvider/cty/values/base.py
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from collections.abc import Iterator
from typing import (
    TYPE_CHECKING,
    Any,
    Generic,
    Self,
    TypeVar,
)

from attrs import define, evolve, field

from pyvider.cty.config.defaults import (
    ERR_CANNOT_COMPARE_CTYVALUE_WITH,
    ERR_CANNOT_COMPARE_DIFFERENT_TYPES,
    ERR_CANNOT_COMPARE_NULL_UNKNOWN,
    ERR_CANNOT_GET_LENGTH_UNKNOWN_VALUE,
    ERR_CANNOT_GET_RAW_VALUE_UNKNOWN,
    ERR_CANNOT_INDEX_UNKNOWN_NULL_VALUE,
    ERR_CANNOT_ITERATE_UNKNOWN_VALUE,
    ERR_UNHASHABLE_TYPE,
    ERR_VALUE_TYPE_NO_LEN,
    ERR_VALUE_TYPE_NOT_COMPARABLE,
    ERR_VALUE_TYPE_NOT_ITERABLE,
    ERR_VALUE_TYPE_NOT_SUBSCRIPTABLE,
)
from pyvider.cty.values.markers import UNREFINED_UNKNOWN

T = TypeVar("T", covariant=True)

if TYPE_CHECKING:
    from pyvider.cty.types import CtyType


@define(frozen=True, slots=True)
class CtyValue(Generic[T]):
    vtype: CtyType[T] = field()
    value: object | None = field(default=None)
    is_unknown: bool = field(default=False)
    is_null: bool = field(default=False)
    marks: frozenset[Any] = field(factory=frozenset)

    def __attrs_post_init__(self) -> None:
        from pyvider.cty.types import CtyDynamic

        if isinstance(self.vtype, CtyDynamic) and isinstance(self.value, CtyValue):
            object.__setattr__(self, "is_unknown", self.value.is_unknown)
            object.__setattr__(self, "is_null", self.value.is_null)

        if self.is_unknown and self.is_null:
            object.__setattr__(self, "is_null", False)
        elif self.is_null and self.value is not None:
            object.__setattr__(self, "value", None)

    @property
    def type(self) -> CtyType[T]:
        return self.vtype

    @property
    def raw_value(self) -> object | None:
        if self.is_unknown:
            error_message = ERR_CANNOT_GET_RAW_VALUE_UNKNOWN
            raise ValueError(error_message)
        if self.is_null:
            return None
        from ..conversion.adapter import cty_to_native

        return cty_to_native(self)  # type: ignore

    def _canonical_sort_key(self) -> tuple[Any, ...]:
        from ..types import (
            CtyBool,
            CtyCapsule,
            CtyList,
            CtyMap,
            CtyNumber,
            CtyObject,
            CtySet,
            CtyString,
            CtyTuple,
        )

        if self.is_null:
            return (0,)
        if self.is_unknown:
            return (1,)

        type_rank = self.type._type_order
        key_prefix = (2, type_rank)

        if isinstance(self.type, CtyBool | CtyNumber | CtyString):
            return (*key_prefix, self.value)

        if (
            isinstance(self.type, CtyList | CtyTuple)
            and self.value is not None
            and hasattr(self.value, "__iter__")
        ):
            return (*key_prefix, *(v._canonical_sort_key() for v in self.value))

        if isinstance(self.type, CtySet) and self.value is not None and hasattr(self.value, "__iter__"):
            sorted_elements = sorted(self.value, key=lambda v: v._canonical_sort_key())
            return (*key_prefix, *(v._canonical_sort_key() for v in sorted_elements))

        if (
            isinstance(self.type, CtyMap | CtyObject)
            and self.value is not None
            and hasattr(self.value, "items")
        ):
            sorted_items = sorted(self.value.items())
            return (
                *key_prefix,
                *((k, v._canonical_sort_key()) for k, v in sorted_items),
            )

        if isinstance(self.type, CtyCapsule):
            return (*key_prefix, repr(self.value))

        # Fallback for any other type
        return (*key_prefix, repr(self.value))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, CtyValue):
            return NotImplemented
        from ..types import CtyCapsuleWithOps

        if isinstance(self.type, CtyCapsuleWithOps) and self.type.equal(other.type) and self.type.equal_fn:
            return self.type.equal_fn(self.value, other.value)

        return (
            self.type.equal(other.type)
            and self.is_unknown == other.is_unknown
            and self.is_null == other.is_null
            and self.marks == other.marks
            and self.value == other.value
        )

    def _check_comparable(self, other: object) -> CtyValue[Any]:
        from ..types import CtyNumber, CtyString

        if not isinstance(other, CtyValue):
            error_message = ERR_CANNOT_COMPARE_CTYVALUE_WITH.format(type_name=type(other).__name__)
            raise TypeError(error_message)
        if self.is_unknown or self.is_null or other.is_unknown or other.is_null:
            error_message = ERR_CANNOT_COMPARE_NULL_UNKNOWN
            raise TypeError(error_message)
        if not self.type.equal(other.type):
            error_message = ERR_CANNOT_COMPARE_DIFFERENT_TYPES.format(type1=self.type, type2=other.type)
            raise TypeError(error_message)
        if not isinstance(self.type, CtyNumber | CtyString):
            error_message = ERR_VALUE_TYPE_NOT_COMPARABLE.format(type=self.type)
            raise TypeError(error_message)
        return other

    def __lt__(self, other: object) -> bool:
        other_val = self._check_comparable(other)
        if hasattr(self.value, "__lt__"):
            return bool(self.value < other_val.value)
        error_message = ERR_VALUE_TYPE_NOT_COMPARABLE.format(type=self.type)
        raise TypeError(error_message)

    def __le__(self, other: object) -> bool:
        other_val = self._check_comparable(other)
        if hasattr(self.value, "__le__"):
            return bool(self.value <= other_val.value)
        error_message = ERR_VALUE_TYPE_NOT_COMPARABLE.format(type=self.type)
        raise TypeError(error_message)

    def __gt__(self, other: object) -> bool:
        other_val = self._check_comparable(other)
        if hasattr(self.value, "__gt__"):
            return bool(self.value > other_val.value)
        error_message = ERR_VALUE_TYPE_NOT_COMPARABLE.format(type=self.type)
        raise TypeError(error_message)

    def __ge__(self, other: object) -> bool:
        other_val = self._check_comparable(other)
        if hasattr(self.value, "__ge__"):
            return bool(self.value >= other_val.value)
        error_message = ERR_VALUE_TYPE_NOT_COMPARABLE.format(type=self.type)
        raise TypeError(error_message)

    def __contains__(self, item: Any) -> bool:
        if self.is_unknown or self.is_null:
            return False
        if hasattr(self.value, "__contains__"):
            return item in self.value
        return bool(self.value == item)

    def __bool__(self) -> bool:
        from pyvider.cty.types import CtyDynamic

        if self.is_unknown or self.is_null:
            return False
        if isinstance(self.vtype, CtyDynamic) and isinstance(self.value, CtyValue):
            return bool(self.value)
        return True

    def __len__(self) -> int:
        from pyvider.cty.types import CtyDynamic, CtyList, CtyMap, CtySet, CtyTuple

        if self.is_unknown:
            error_message = ERR_CANNOT_GET_LENGTH_UNKNOWN_VALUE
            raise TypeError(error_message)
        if isinstance(self.vtype, CtyDynamic) and isinstance(self.value, CtyValue):
            return len(self.value)
        if self.is_null:
            return 0
        if isinstance(self.vtype, CtyList | CtyMap | CtySet | CtyTuple) and hasattr(self.value, "__len__"):
            return len(self.value)
        error_message = ERR_VALUE_TYPE_NO_LEN.format(type_name=self.vtype.__class__.__name__)
        raise TypeError(error_message)

    def __iter__(self) -> Iterator[Any]:
        from pyvider.cty.types import CtyList, CtyMap, CtySet, CtyTuple

        if self.is_unknown:
            error_message = ERR_CANNOT_ITERATE_UNKNOWN_VALUE
            raise TypeError(error_message)
        if self.is_null:
            return iter([])
        if isinstance(self.vtype, CtyList | CtySet | CtyTuple) and hasattr(self.value, "__iter__"):
            return iter(self.value)
        if isinstance(self.vtype, CtyMap) and hasattr(self.value, "values"):
            return iter(self.value.values())

        error_message = ERR_VALUE_TYPE_NOT_ITERABLE.format(type_name=self.vtype.__class__.__name__)
        raise TypeError(error_message)

    def __getitem__(self, key: Any) -> CtyValue[Any]:
        from ..types import CtyList, CtyMap, CtyObject, CtyTuple

        if self.is_unknown or self.is_null:
            error_message = ERR_CANNOT_INDEX_UNKNOWN_NULL_VALUE
            raise TypeError(error_message)
        if isinstance(self.vtype, CtyObject):
            if not isinstance(key, str):
                raise TypeError(f"Object attribute name must be a string, got {type(key).__name__}")
            return self.vtype.get_attribute(self, key)
        if isinstance(self.vtype, CtyList):
            if not isinstance(self.value, list | tuple):
                raise TypeError(f"CtyList value is not a list/tuple, but {type(self.value).__name__}")
            if isinstance(key, slice):
                return CtyValue(vtype=self.vtype, value=tuple(self.value[key]))
            return self.vtype.element_at(self, key)
        if isinstance(self.vtype, CtyTuple):
            return self.vtype.element_at(self, key)
        if isinstance(self.vtype, CtyMap):
            return self.vtype.get(self, key)  # type: ignore[arg-type]
        error_message = ERR_VALUE_TYPE_NOT_SUBSCRIPTABLE.format(type_name=self.vtype.__class__.__name__)
        raise TypeError(error_message)

    def __hash__(self) -> int:
        from pyvider.cty.types import (
            CtyCapsuleWithOps,
            CtyList,
            CtyMap,
            CtyObject,
            CtySet,
        )

        if isinstance(self.type, CtyCapsuleWithOps) and self.type.hash_fn:
            return self.type.hash_fn(self.value)

        if isinstance(self.vtype, CtyList | CtySet | CtyMap | CtyObject):
            error_message = ERR_UNHASHABLE_TYPE.format(vtype=self.vtype.ctype)
            raise TypeError(error_message)

        if self.is_unknown or self.is_null:
            return hash((self.vtype, self.is_unknown, self.is_null, self.marks))
        return hash((self.vtype, self.is_unknown, self.is_null, self.marks, self.value))

    def has_mark(self, mark: object) -> bool:
        return mark in self.marks

    def mark(self, mark: object) -> Self:
        return evolve(self, marks=self.marks.union({mark}))

    def with_marks(self, marks_to_add: set[Any]) -> Self:
        return evolve(self, marks=self.marks.union(marks_to_add))

    def unmark(self) -> tuple[Self, frozenset[Any]]:
        unmarked_value = evolve(self, marks=frozenset())
        return unmarked_value, self.marks

    def is_true(self) -> bool:
        from pyvider.cty.types import CtyDynamic

        if isinstance(self.vtype, CtyDynamic) and isinstance(self.value, CtyValue):
            return self.value.is_true()
        return self.value is True

    def is_false(self) -> bool:
        from pyvider.cty.types import CtyDynamic

        if isinstance(self.vtype, CtyDynamic) and isinstance(self.value, CtyValue):
            return self.value.is_false()
        return self.value is False

    def is_empty(self) -> bool:
        return not self.value if hasattr(self.value, "__len__") else False

    def with_key(self, key: str, value: Any) -> Self:
        from ..types import CtyMap

        if not isinstance(self.vtype, CtyMap):
            raise TypeError("'.with_key()' can only be used on CtyMap values.")
        if not isinstance(self.value, dict):
            raise TypeError("Internal value of CtyMap must be a dict.")
        new_dict = self.value.copy()
        new_dict[key] = value
        # validate() returns CtyValue[Any] due to .value: object limitation
        return self.vtype.validate(new_dict)  # type: ignore[no-any-return]

    def without_key(self, key: str) -> Self:
        from ..types import CtyMap

        if not isinstance(self.vtype, CtyMap):
            raise TypeError("'.without_key()' can only be used on CtyMap values.")
        if not isinstance(self.value, dict):
            raise TypeError("Internal value of CtyMap must be a dict.")
        if key not in self.value:
            return self
        new_dict = self.value.copy()
        del new_dict[key]
        # validate() returns CtyValue[Any] due to .value: object limitation
        return self.vtype.validate(new_dict)  # type: ignore[no-any-return]

    def append(self, value: Any) -> Self:
        from ..types import CtyList

        if not isinstance(self.vtype, CtyList):
            raise TypeError("'.append()' can only be used on CtyList values.")
        if not isinstance(self.value, list | tuple):
            raise TypeError("Internal value of CtyList must be a list or tuple.")
        new_list = list(self.value)
        new_list.append(value)
        # validate() returns CtyValue[Any] due to .value: object limitation
        return self.vtype.validate(new_list)  # type: ignore[no-any-return]

    def with_element_at(self, index: int, value: Any) -> Self:
        from ..types import CtyList

        if not isinstance(self.vtype, CtyList):
            raise TypeError("'.with_element_at()' can only be used on CtyList values.")
        if not isinstance(self.value, list | tuple):
            raise TypeError("Internal value of CtyList must be a list or tuple.")
        new_list = list(self.value)
        if not (-len(new_list) <= index < len(new_list)):
            raise IndexError("list index out of range")
        new_list[index] = value
        # validate() returns CtyValue[Any] due to .value: object limitation
        return self.vtype.validate(new_list)  # type: ignore[no-any-return]

    @classmethod
    def unknown(cls, vtype: CtyType[Any], value: Any = UNREFINED_UNKNOWN) -> CtyValue[Any]:
        return cls(vtype=vtype, is_unknown=True, value=value)

    @classmethod
    def null(cls, vtype: CtyType[Any]) -> CtyValue[Any]:
        return cls(vtype=vtype, is_null=True)


# 🐍⛓️💰🪄
