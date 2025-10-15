# src/pyvider/cty/types/structural/object.py
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Any, ClassVar
import unicodedata

from attrs import define, field
from provide.foundation.errors import error_boundary

from pyvider.cty.conversion._utils import _attrs_to_dict_safe
from pyvider.cty.exceptions import (
    CtyAttributeValidationError,
    CtyTypeMismatchError,
    CtyValidationError,
    InvalidTypeError,
)
from pyvider.cty.path import CtyPath, GetAttrStep
from pyvider.cty.types.base import CtyType
from pyvider.cty.validation.recursion import with_recursion_detection
from pyvider.cty.values import CtyValue


@define(frozen=True, slots=True)
class CtyObject(CtyType[dict[str, object]]):
    ctype: ClassVar[str] = "object"
    _type_order: ClassVar[int] = 7
    attribute_types: dict[str, CtyType[Any]] = field(factory=dict)
    optional_attributes: frozenset[str] = field(factory=frozenset, converter=frozenset)

    def __attrs_post_init__(self) -> None:
        for name, attr_type in self.attribute_types.items():
            if not isinstance(attr_type, CtyType):
                raise InvalidTypeError(
                    f"Attribute '{name}' must be a CtyType, but got {type(attr_type).__name__}"
                )

    def __hash__(self) -> int:
        # Use a recursive hashing approach that safely handles nested objects
        def safe_hash_type(cty_type: CtyType[Any]) -> int:
            if hasattr(cty_type, "ctype") and cty_type.ctype == "object":
                # For nested objects, use a simpler hash to avoid recursion
                return hash((cty_type.ctype, tuple(sorted(cty_type.attribute_types.keys()))))
            return hash(cty_type)

        attr_hashes = tuple(
            (name, safe_hash_type(attr_type)) for name, attr_type in sorted(self.attribute_types.items())
        )
        return hash((self.ctype, attr_hashes, self.optional_attributes))

    def __repr__(self) -> str:
        # Provide a safe representation that doesn't recurse infinitely
        attr_keys = sorted(self.attribute_types.keys())
        optional_list = sorted(self.optional_attributes)
        if len(attr_keys) > 5:
            # Truncate long attribute lists
            attr_display = f"{attr_keys[:5]}...+{len(attr_keys) - 5} more"
        else:
            attr_display = str(attr_keys)

        optional_display = f", optional={optional_list}" if optional_list else ""
        return f"CtyObject(attributes={attr_display}{optional_display})"

    @with_recursion_detection
    def validate(self, value: object) -> CtyValue[dict[str, Any]]:  # noqa: C901
        if isinstance(value, CtyValue):
            if self.equal(value.type) and isinstance(value.value, dict):
                return value  # Fast path
            if value.is_unknown:
                return CtyValue.unknown(self)
            if value.is_null:
                return CtyValue.null(self)
            value = value.value

        if value is None:
            return CtyValue.null(self)
        from pyvider.cty.types.structural.dynamic import CtyDynamic

        unknown_optionals = self.optional_attributes - set(self.attribute_types.keys())
        if unknown_optionals:
            raise CtyAttributeValidationError(
                f"Unknown optional attributes: {', '.join(sorted(list(unknown_optionals)))}"
            )

        if hasattr(type(value), "__attrs_attrs__"):
            value = _attrs_to_dict_safe(value)
        if not isinstance(value, dict):
            raise CtyAttributeValidationError(
                f"Expected a dictionary for CtyObject, got {type(value).__name__}"
            )

        # Normalize keys to NFC before validation to ensure consistency.
        value = {unicodedata.normalize("NFC", k): v for k, v in value.items()}

        validated_attrs: dict[str, CtyValue[Any]] = {}
        all_expected_attrs = set(self.attribute_types.keys())
        unknown = set(value.keys()) - all_expected_attrs
        if unknown:
            raise CtyAttributeValidationError(f"Unknown attributes: {', '.join(sorted(list(unknown)))}")

        for name, attr_type in self.attribute_types.items():
            with error_boundary(
                context={
                    "operation": "object_attribute_validation",
                    "attribute_name": name,
                    "attribute_type": str(attr_type),
                    "is_optional": name in self.optional_attributes,
                }
            ):
                path = CtyPath(steps=[GetAttrStep(name)])
                if name not in value:
                    if name in self.optional_attributes:
                        validated_attrs[name] = CtyValue.null(attr_type)
                        continue
                    raise CtyAttributeValidationError("Missing required attribute", value=None, path=path)

                raw_attr_value = value.get(name)
                try:
                    existing_marks: frozenset[Any] = frozenset()
                    if isinstance(raw_attr_value, CtyValue):
                        existing_marks = raw_attr_value.marks

                    validated_attr = attr_type.validate(raw_attr_value)

                    if existing_marks:
                        validated_attr = validated_attr.with_marks(existing_marks)  # type: ignore

                except CtyValidationError as e:
                    new_path = CtyPath(steps=[GetAttrStep(name)] + (e.path.steps if e.path else []))
                    raise CtyAttributeValidationError(
                        e.message,
                        value=raw_attr_value,
                        path=new_path,
                        original_exception=e,
                    ) from e

                if (
                    name not in self.optional_attributes
                    and validated_attr.is_null
                    and not isinstance(attr_type, CtyDynamic)
                ):
                    raise CtyAttributeValidationError("Attribute cannot be null", value=None, path=path)

                validated_attrs[name] = validated_attr

        is_unknown = any(v.is_unknown for v in validated_attrs.values())
        return CtyValue(vtype=self, value=validated_attrs, is_unknown=is_unknown)

    def get_attribute(self, obj_value: CtyValue[Any], name: str) -> CtyValue[Any]:
        if not isinstance(obj_value, CtyValue):
            raise CtyTypeMismatchError("get_attribute requires a CtyValue object")
        if not self.has_attribute(name):
            raise CtyAttributeValidationError(f"Object has no attribute '{name}'", path=CtyPath.get_attr(name))
        if obj_value.is_unknown:
            return CtyValue.unknown(self.attribute_types[name])
        if obj_value.is_null:
            return CtyValue.null(self.attribute_types[name])
        if isinstance(obj_value.value, dict):
            return obj_value.value.get(name, CtyValue.null(self.attribute_types[name]))  # type: ignore
        raise CtyTypeMismatchError("CtyObject value is not a dict")

    def has_attribute(self, name: str) -> bool:
        return name in self.attribute_types

    def equal(self, other: CtyType[Any]) -> bool:
        if not isinstance(other, CtyObject):
            return False
        if self.optional_attributes != other.optional_attributes:
            return False
        if self.attribute_types.keys() != other.attribute_types.keys():
            return False
        return all(self.attribute_types[key].equal(other.attribute_types[key]) for key in self.attribute_types)

    def usable_as(self, other: CtyType[Any]) -> bool:
        from pyvider.cty.types.structural import CtyDynamic

        if isinstance(other, CtyDynamic):
            return True
        if not isinstance(other, CtyObject):
            return False
        other_attrs = set(other.attribute_types.keys())
        self_attrs = set(self.attribute_types.keys())
        if not other_attrs.issubset(self_attrs):
            return False
        self_required = self_attrs - self.optional_attributes
        other_required = other_attrs - other.optional_attributes
        if not other_required.issubset(self_required):
            return False
        return all(
            self.attribute_types[name].usable_as(other_type)
            for name, other_type in other.attribute_types.items()
        )

    def _to_wire_json(self) -> Any:
        # Sort attributes alphabetically to match go-cty behavior for consistent wire format
        attrs_json = {
            name: attr_type._to_wire_json() for name, attr_type in sorted(self.attribute_types.items())
        }
        return [self.ctype, attrs_json]

    def is_primitive_type(self) -> bool:
        return False


# 🐍⛓️🧱🪄
