# src/pyvider/cty/path/base.py
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, TypeVar

from attrs import define, field

from pyvider.cty.exceptions import (
    AttributePathError,
    CtyValidationError,
)
from pyvider.cty.types import CtyType
from pyvider.cty.values import CtyValue

T = TypeVar("T")


class PathStep(ABC):
    @abstractmethod
    def apply(self, value: CtyValue[Any]) -> CtyValue[Any]:
        pass

    @abstractmethod
    def apply_type(self, vtype: CtyType[Any]) -> CtyType[Any]:
        pass

    @abstractmethod
    def __str__(self) -> str:
        pass


@define(frozen=True)
class GetAttrStep(PathStep):
    name: str = field()

    @name.validator
    def _validate_name(self, attribute: str, value: str) -> None:
        if not value:
            raise ValueError("Attribute name cannot be empty")

    def apply(self, value: CtyValue[Any]) -> CtyValue[Any]:
        if value.is_null:
            raise AttributePathError(f"Cannot get attribute '{self.name}' from null value")
        from pyvider.cty.types.structural import CtyObject

        if isinstance(value.type, CtyObject):
            return value.type.get_attribute(value, self.name)
        raise AttributePathError(
            f"Cannot get attribute from non-object value of type {value.type.__class__.__name__}"
        )

    def apply_type(self, vtype: CtyType[Any]) -> CtyType[Any]:
        from pyvider.cty.types.structural import CtyObject

        if not isinstance(vtype, CtyObject):
            raise AttributePathError(f"Cannot get attribute from non-object type {vtype.__class__.__name__}")
        if not vtype.has_attribute(self.name):
            raise AttributePathError(f"Object type has no attribute {self.name}")
        return vtype.attribute_types[self.name]

    def __str__(self) -> str:
        return f".{self.name}"


@define(frozen=True)
class IndexStep(PathStep):
    index: int = field()

    def apply(self, value: CtyValue[Any]) -> CtyValue[Any]:
        if value.is_null:
            raise AttributePathError("Cannot index into null value")
        if value.is_unknown:
            return CtyValue.unknown(self.apply_type(value.type))
        from pyvider.cty.types.collections import CtyList
        from pyvider.cty.types.structural import CtyDynamic, CtyTuple

        if isinstance(value.type, CtyList | CtyTuple):
            return value.type.element_at(value, self.index)
        if isinstance(value.type, CtyDynamic) and isinstance(value.value, CtyValue):
            result = self.apply(value.value)
            return CtyValue(result.type, result.value)
        raise AttributePathError(f"Cannot index into value of type {type(value.type).__name__}")

    def apply_type(self, vtype: CtyType[Any]) -> CtyType[Any]:
        from pyvider.cty.types.collections import CtyList
        from pyvider.cty.types.structural import CtyDynamic, CtyTuple

        if isinstance(vtype, CtyList):
            return vtype.element_type
        if isinstance(vtype, CtyTuple):
            try:
                return vtype.element_types[self.index]
            except IndexError as e:
                raise AttributePathError(f"Tuple index {self.index} out of bounds") from e
        if isinstance(vtype, CtyDynamic):
            return CtyDynamic()
        raise AttributePathError(f"Cannot index into non-collection type {vtype.__class__.__name__}")

    def __str__(self) -> str:
        return f"[{self.index}]"


@define(frozen=True)
class KeyStep(PathStep):
    key: object = field()

    def apply(self, value: CtyValue[Any]) -> CtyValue[Any]:
        if value.is_null:
            raise AttributePathError("Cannot get key from null value")
        if value.is_unknown:
            return CtyValue.unknown(self.apply_type(value.type))
        from pyvider.cty.types.collections import CtyMap
        from pyvider.cty.types.structural import CtyDynamic

        if isinstance(value.type, CtyMap):
            return value.type.get(value, self.key)
        if isinstance(value.type, CtyDynamic) and isinstance(value.value, CtyValue):
            result = self.apply(value.value)
            return CtyValue(result.type, result.value)
        raise AttributePathError(
            f"Cannot get key from non-map/non-dynamic value of type {type(value.type).__name__}"
        )

    def apply_type(self, vtype: CtyType[Any]) -> CtyType[Any]:
        from pyvider.cty.types import CtyString
        from pyvider.cty.types.collections import CtyMap
        from pyvider.cty.types.structural import CtyDynamic

        if isinstance(vtype, CtyDynamic):
            return CtyDynamic()
        if not isinstance(vtype, CtyMap):
            raise AttributePathError(f"Cannot get key from non-map type {vtype.__class__.__name__}")
        try:
            CtyString().validate(self.key)
        except CtyValidationError as e:
            raise AttributePathError(f"Invalid key for map: {self.key!r} is not a valid string") from e
        return vtype.element_type

    def __str__(self) -> str:
        return f"[{self.key!r}]"


@define
class CtyPath:
    steps: list[PathStep] = field(factory=list)

    @classmethod
    def empty(cls) -> CtyPath:
        return cls([])

    @classmethod
    def get_attr(cls, name: str) -> CtyPath:
        return cls([GetAttrStep(name)])

    @classmethod
    def index(cls, index: int) -> CtyPath:
        return cls([IndexStep(index)])

    @classmethod
    def key(cls, key: object) -> CtyPath:
        return cls([KeyStep(key)])

    def child(self, name: str) -> CtyPath:
        return CtyPath([*self.steps, GetAttrStep(name)])

    def index_step(self, index: int) -> CtyPath:
        return CtyPath([*self.steps, IndexStep(index)])

    def key_step(self, key: object) -> CtyPath:
        return CtyPath([*self.steps, KeyStep(key)])

    def apply_path(self, value: object) -> CtyValue[Any]:
        if not self.steps:
            if isinstance(value, CtyValue):
                return value
            raise AttributePathError("Cannot return non-CtyValue from apply_path")
        if not isinstance(value, CtyValue):
            raise AttributePathError(f"Cannot apply path to non-CtyValue: {type(value).__name__}")
        current = value
        for i, step in enumerate(self.steps):
            try:
                current = step.apply(current)
            except AttributePathError as e:
                raise AttributePathError(f"Error at step {i + 1} ({step}): {e}") from e
        return current

    def apply_path_type(self, vtype: CtyType[Any]) -> CtyType[Any]:
        if not self.steps:
            return vtype
        current = vtype
        for i, step in enumerate(self.steps):
            try:
                current = step.apply_type(current)
            except AttributePathError as e:
                raise AttributePathError(f"Error at type step {i + 1} ({step}): {e}") from e
        return current

    def string(self) -> str:
        if not self.steps:
            return "(root)"

        path_str = ""
        for i, step in enumerate(self.steps):
            current_step_str = str(step)
            if i == 0 and isinstance(step, GetAttrStep):
                path_str += current_step_str[1:]  # Strip leading dot
            else:
                path_str += current_step_str

        return path_str

    def __str__(self) -> str:
        return self.string()


# 🐍⛓️➡️🪄
