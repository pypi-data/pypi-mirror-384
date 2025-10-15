# src/pyvider/cty/types/structural/dynamic.py
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, ClassVar

from attrs import define

from pyvider.cty.exceptions import CtyValidationError, DeserializationError
from pyvider.cty.types.base import CtyType
from pyvider.cty.validation.recursion import with_recursion_detection

if TYPE_CHECKING:
    from pyvider.cty.values import CtyValue


@define(frozen=True, slots=True)
class CtyDynamic(CtyType[object]):
    """Represents a dynamic type that can hold any CtyValue."""

    ctype: ClassVar[str] = "dynamic"
    _type_order: ClassVar[int] = 9

    @with_recursion_detection
    def validate(self, value: object) -> CtyValue[Any]:
        """
        Validates a raw Python value for a dynamic type. The result is always a
        CtyValue of type CtyDynamic, which wraps the inferred concrete value.
        """
        from pyvider.cty.conversion.raw_to_cty import infer_cty_type_from_raw
        from pyvider.cty.parser import parse_tf_type_to_ctytype
        from pyvider.cty.values import CtyValue

        if isinstance(value, CtyValue):
            if isinstance(value.type, CtyDynamic):
                return value
            return CtyValue(vtype=self, value=value)

        if value is None:
            return CtyValue.null(self)

        if isinstance(value, list) and len(value) == 2 and isinstance(value[0], bytes):
            try:
                type_spec = json.loads(value[0].decode("utf-8"))
                actual_type = parse_tf_type_to_ctytype(type_spec)
                concrete_value = actual_type.validate(value[1])
                return CtyValue(vtype=self, value=concrete_value)
            except json.JSONDecodeError as e:
                raise DeserializationError(
                    "Failed to decode dynamic value type spec from JSON during validation"
                ) from e
            except CtyValidationError as e:
                raise e

        inferred_type = infer_cty_type_from_raw(value)
        concrete_value = inferred_type.validate(value)
        return CtyValue(vtype=self, value=concrete_value)

    def equal(self, other: CtyType[Any]) -> bool:
        return isinstance(other, CtyDynamic)

    def usable_as(self, other: CtyType[Any]) -> bool:
        return isinstance(other, CtyDynamic)

    def _to_wire_json(self) -> Any:
        return self.ctype

    def is_dynamic_type(self) -> bool:
        return True

    def __str__(self) -> str:
        return "dynamic"


# 🐍⛓️🧱🪄
