# src/pyvider/cty/exceptions/validation.py
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from provide.foundation.errors import ValidationError as FoundationValidationError

if TYPE_CHECKING:
    from pyvider.cty.path import CtyPath
    from pyvider.cty.types import CtyType


class CtyValidationError(FoundationValidationError):
    """Base exception for all validation errors.

    Inherits from foundation's ValidationError for enhanced diagnostics
    and automatic retry/circuit breaker support where applicable.
    """

    def __init__(
        self,
        message: str,
        value: object = None,
        type_name: str | None = None,
        path: CtyPath | None = None,
        **kwargs: Any,
    ) -> None:
        self.value = value
        self.type_name = type_name
        self.path = path
        self.message = message

        # Add rich context to foundation error with more detailed information
        context = kwargs.setdefault("context", {})

        # Core CTY context
        if type_name:
            context["cty.type"] = type_name
        if path:
            context["cty.path"] = str(path)
            context["cty.path_depth"] = len(path.steps) if path else 0

        # Value context with safe representation
        if value is not None:
            context["cty.value_type"] = type(value).__name__
            # Safe value representation for debugging (truncated to avoid huge objects)
            try:
                value_repr = repr(value)
                context["cty.value_repr"] = value_repr[:200] + "..." if len(value_repr) > 200 else value_repr
            except Exception:
                context["cty.value_repr"] = f"<repr failed for {type(value).__name__}>"

        # Add validation context if available
        context["cty.validation_stage"] = "type_validation"

        super().__init__(self.message, **kwargs)

    def _default_code(self) -> str:
        return "CTY_VALIDATION_ERROR"

    def __str__(self) -> str:
        """Creates a user-friendly, path-aware error message."""
        path_str = str(self.path) if self.path and self.path.steps else ""
        core_message = self.message

        if path_str and path_str != "(root)":
            return f"At {path_str}: {core_message}"

        return core_message


def _get_type_name_from_original(original_exc: CtyValidationError | None, default: str) -> str:
    """Helper to safely extract type_name from an original exception."""
    if original_exc and original_exc.type_name:
        return original_exc.type_name
    return default


# --- Primitive Validation Errors ---
class CtyBoolValidationError(CtyValidationError):
    def __init__(
        self,
        message: str,
        value: object = None,
        path: CtyPath | None = None,
        **kwargs: Any,
    ) -> None:
        # Add bool-specific context
        context = kwargs.setdefault("context", {})
        context["cty.primitive_type"] = "bool"
        context["cty.validation_stage"] = "bool_validation"

        super().__init__(f"Boolean validation error: {message}", value, "Boolean", path, **kwargs)


class CtyNumberValidationError(CtyValidationError):
    def __init__(
        self,
        message: str,
        value: object = None,
        path: CtyPath | None = None,
        **kwargs: Any,
    ) -> None:
        # Add number-specific context
        context = kwargs.setdefault("context", {})
        context["cty.primitive_type"] = "number"
        context["cty.validation_stage"] = "number_validation"

        # Add numeric value analysis if applicable
        if isinstance(value, (int, float)):
            context["cty.numeric_value"] = str(value)
            context["cty.numeric_type"] = type(value).__name__

        super().__init__(f"Number validation error: {message}", value, "Number", path, **kwargs)


class CtyStringValidationError(CtyValidationError):
    def __init__(
        self,
        message: str,
        value: object = None,
        path: CtyPath | None = None,
        **kwargs: Any,
    ) -> None:
        # Add string-specific context
        context = kwargs.setdefault("context", {})
        context["cty.primitive_type"] = "string"
        context["cty.validation_stage"] = "string_validation"

        # Add string analysis if applicable
        if isinstance(value, str):
            context["cty.string_length"] = len(value)
            context["cty.string_encoding"] = "utf-8"  # Assumed for Python strings

        super().__init__(f"String validation error: {message}", value, "String", path, **kwargs)


# --- Collection Validation Errors ---
class CtyCollectionValidationError(CtyValidationError):
    """Base for collection-related validation errors."""


class CtyListValidationError(CtyCollectionValidationError):
    def __init__(
        self,
        message: str,
        value: object = None,
        path: CtyPath | None = None,
        *,
        original_exception: CtyValidationError | None = None,
        **kwargs: Any,
    ) -> None:
        # Add list-specific context
        context = kwargs.setdefault("context", {})
        context["cty.collection_type"] = "list"

        if isinstance(value, (list, tuple)):
            context["cty.collection_length"] = len(value)

        if original_exception:
            context["cty.nested_error"] = type(original_exception).__name__

        super().__init__(
            message,
            value,
            _get_type_name_from_original(original_exception, "List"),
            path,
            **kwargs,
        )


class CtyMapValidationError(CtyCollectionValidationError):
    def __init__(
        self,
        message: str,
        value: object = None,
        path: CtyPath | None = None,
        *,
        original_exception: CtyValidationError | None = None,
        **kwargs: Any,
    ) -> None:
        # Add map-specific context
        context = kwargs.setdefault("context", {})
        context["cty.collection_type"] = "map"

        if isinstance(value, dict):
            context["cty.collection_size"] = len(value)

        if original_exception:
            context["cty.nested_error"] = type(original_exception).__name__

        super().__init__(
            message,
            value,
            _get_type_name_from_original(original_exception, "Map"),
            path,
            **kwargs,
        )


class CtySetValidationError(CtyCollectionValidationError):
    def __init__(
        self,
        message: str,
        value: object = None,
        path: CtyPath | None = None,
        *,
        original_exception: CtyValidationError | None = None,
        **kwargs: Any,
    ) -> None:
        # Add set-specific context
        context = kwargs.setdefault("context", {})
        context["cty.collection_type"] = "set"

        if isinstance(value, (set, frozenset)):
            context["cty.collection_size"] = len(value)
            context["cty.set_type"] = type(value).__name__

        if original_exception:
            context["cty.nested_error"] = type(original_exception).__name__

        super().__init__(
            message,
            value,
            _get_type_name_from_original(original_exception, "Set"),
            path,
            **kwargs,
        )


class CtyTupleValidationError(CtyCollectionValidationError):
    def __init__(
        self,
        message: str,
        value: object = None,
        path: CtyPath | None = None,
        *,
        original_exception: CtyValidationError | None = None,
        **kwargs: Any,
    ) -> None:
        # Add tuple-specific context
        context = kwargs.setdefault("context", {})
        context["cty.collection_type"] = "tuple"

        if isinstance(value, tuple):
            context["cty.collection_length"] = len(value)
            context["cty.tuple_element_types"] = [type(item).__name__ for item in value]

        if original_exception:
            context["cty.nested_error"] = type(original_exception).__name__

        super().__init__(
            message,
            value,
            _get_type_name_from_original(original_exception, "Tuple"),
            path,
            **kwargs,
        )


# --- Structural and Type Definition Errors ---
class CtyAttributeValidationError(CtyValidationError):
    def __init__(
        self,
        message: str,
        value: object = None,
        path: CtyPath | None = None,
        *,
        original_exception: CtyValidationError | None = None,
        **kwargs: Any,
    ) -> None:
        # Add object-specific context
        context = kwargs.setdefault("context", {})
        context["cty.validation_type"] = "object_attribute"

        if path and path.steps:
            # Extract attribute name from path
            first_step = path.steps[0]
            if hasattr(first_step, "attribute_name"):
                context["cty.attribute_name"] = first_step.attribute_name

        if original_exception:
            context["cty.nested_error"] = type(original_exception).__name__

        super().__init__(
            message,
            value,
            _get_type_name_from_original(original_exception, "Object"),
            path,
            **kwargs,
        )


class CtyTypeValidationError(CtyValidationError):
    def __init__(
        self,
        message: str,
        type_name: str | None = None,
        path: CtyPath | None = None,
        **kwargs: Any,
    ) -> None:
        # Add type definition context
        context = kwargs.setdefault("context", {})
        context["cty.validation_stage"] = "type_definition"
        context["cty.type_category"] = "meta"

        super().__init__(message, type_name=type_name or "TypeDefinition", path=path, **kwargs)


class CtyTypeMismatchError(CtyValidationError):
    def __init__(
        self,
        message: str,
        actual_type: CtyType[Any] | None = None,
        expected_type: CtyType[Any] | None = None,
        path: CtyPath | None = None,
        **kwargs: Any,
    ) -> None:
        self.actual_type = actual_type
        self.expected_type = expected_type

        # Add type mismatch context
        context = kwargs.setdefault("context", {})
        context["cty.validation_stage"] = "type_mismatch"
        context["cty.error_category"] = "type_compatibility"

        if actual_type:
            context["cty.actual_type"] = str(actual_type)
        if expected_type:
            context["cty.expected_type"] = str(expected_type)

        type_info = f"Expected {expected_type}, got {actual_type}"
        full_message = f"{message} ({type_info})"
        super().__init__(full_message, path=path, **kwargs)


# 🐍⛓️🐛🪄
