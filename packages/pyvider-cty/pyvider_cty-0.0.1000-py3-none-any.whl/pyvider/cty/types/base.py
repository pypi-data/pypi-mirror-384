# src/pyvider/cty/types/base.py
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    Generic,
    Protocol,
    TypeVar,
    runtime_checkable,
)

from attrs import define

# Forward reference to CtyValue to avoid importing it directly at runtime
if TYPE_CHECKING:
    from pyvider.cty.values.base import CtyValue

T_co = TypeVar("T_co", covariant=True)
T = TypeVar("T")


@runtime_checkable
class CtyTypeProtocol(Protocol[T_co]):
    """Protocol defining the essential interface of a CtyType."""

    def validate(self, value: object) -> CtyValue[T_co]: ...
    def equal(self, other: Any) -> bool: ...
    def usable_as(self, other: Any) -> bool: ...
    def is_primitive_type(self) -> bool: ...


# The concrete ABC now implements the protocol
@define(slots=True)
class CtyType(CtyTypeProtocol[T], Generic[T], ABC):
    """
    Generic abstract base class for all Cty types.
    """

    ctype: ClassVar[str | None] = None
    _type_order: ClassVar[int] = 99

    @abstractmethod
    def validate(self, value: object) -> CtyValue[T]:
        pass

    @abstractmethod
    def equal(self, other: Any) -> bool:
        pass

    @abstractmethod
    def usable_as(self, other: Any) -> bool:
        pass

    @abstractmethod
    def _to_wire_json(self) -> Any:
        """Abstract method for JSON wire format encoding."""
        pass

    def is_primitive_type(self) -> bool:
        return False

    def is_dynamic_type(self) -> bool:
        """Returns True if this type is CtyDynamic."""
        return False

    def __eq__(self, other: object) -> bool:
        if isinstance(other, CtyType):
            return self.equal(other)
        return NotImplemented

    def __hash__(self) -> int:
        return hash(repr(self))

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"


# 🐍⛓️🧱🪄
