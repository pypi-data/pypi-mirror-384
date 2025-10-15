# src/pyvider/cty/exceptions/conversion.py
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Any

from pyvider.cty.exceptions.base import CtyError

# pyvider/cty/exceptions/conversion.py
"""
Defines exceptions related to CTY type and value conversions.
"""


class CtyConversionError(CtyError):
    """Base for CTY value or type conversion errors."""

    def __init__(
        self,
        message: str,
        *,
        source_value: object | None = None,
        target_type: object | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Initializes the CtyConversionError.

        Args:
            message: The base error message.
            source_value: The value that was being converted.
            target_type: The intended target type of the conversion.
            **kwargs: Additional foundation error context.
        """
        self.source_value = source_value
        self.target_type = target_type

        # Add rich conversion context
        context = kwargs.setdefault("context", {})
        context["cty.operation"] = "conversion"
        context["cty.error_category"] = "type_conversion"

        # Build message with old format for compatibility
        context_parts = []
        if source_value is not None:
            context_parts.append(f"source_type={type(source_value).__name__}")
            # Also add to foundation context
            context["conversion.source_type"] = type(source_value).__name__
            context["conversion.source_value_type"] = type(source_value).__name__

            # Add value analysis for better debugging
            if hasattr(source_value, "type") and hasattr(source_value, "is_null"):
                context["conversion.source_cty_type"] = str(source_value.type)
                context["conversion.source_is_null"] = source_value.is_null
                if hasattr(source_value, "is_unknown"):
                    context["conversion.source_is_unknown"] = source_value.is_unknown

        if target_type is not None:
            target_name = target_type.__name__ if hasattr(target_type, "__name__") else str(target_type)
            context_parts.append(f"target_type={target_name}")
            context["conversion.target_type"] = target_name
            context["conversion.target_type_str"] = str(target_type)

        if context_parts:
            message = f"{message} ({', '.join(context_parts)})"

        super().__init__(message, **kwargs)

    def _default_code(self) -> str:
        return "CTY_CONVERSION_ERROR"


class CtyTypeConversionError(CtyConversionError):
    """CTY type representation conversion failure."""

    def __init__(
        self,
        message: str,
        *,
        type_name: str | None = None,
        source_value: object | None = None,
        target_type: object | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Initializes the CtyTypeConversionError.

        Args:
            message: The base error message.
            type_name: The name of the CTY type involved in the conversion failure.
            source_value: The value that was being converted.
            target_type: The intended target type of the conversion.
        """
        self.type_name = type_name

        # Add type-specific context
        context = kwargs.setdefault("context", {})
        context["cty.conversion_category"] = "type_representation"

        if type_name:
            context["cty.failing_type"] = type_name
            message = f'CTY Type "{type_name}" representation conversion failed: {message}'

        super().__init__(message, source_value=source_value, target_type=target_type, **kwargs)


class CtyTypeParseError(CtyConversionError):
    """Raised when a CTY type string cannot be parsed."""

    def __init__(self, message: str, type_string: str, **kwargs: Any) -> None:
        self.type_string = type_string

        # Add parsing context
        context = kwargs.setdefault("context", {})
        context["cty.conversion_category"] = "type_parsing"
        context["cty.parse_input"] = str(type_string)[:100]  # Truncate for safety
        context["cty.parse_input_type"] = type(type_string).__name__

        full_message = f"{message}: '{type_string}'"
        super().__init__(full_message, source_value=type_string, **kwargs)


__all__ = ["CtyConversionError", "CtyTypeConversionError", "CtyTypeParseError"]

# 🐍⛓️🐛🪄
