# src/pyvider/cty/validation/__init__.py
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Any

from pyvider.cty.validation.recursion import (
    RecursionContext,
    RecursionDetector,
    clear_recursion_context,
    get_recursion_context,
    with_recursion_detection,
)

"""
Advanced validation utilities for CTY.

This module provides sophisticated validation capabilities designed for
production IaC requirements including advanced recursion detection,
performance monitoring, and comprehensive diagnostics.
"""


# Define validate_config here to avoid circular imports
def validate_config(schema: Any, config: Any) -> None:
    """
    Validates a configuration against a CtyType schema.

    This function serves as the primary entry point for validation,
    delegating to the `validate` method of the provided schema. It allows
    the CtyValidationError to propagate, which is the expected contract
    for testing and low-level framework integration.

    Args:
        schema: The CtyType object to validate against.
        config: The raw Python data to validate.

    Raises:
        CtyValidationError: If the configuration does not conform to the schema.
    """
    # The schema (a CtyType instance) has the validation logic.
    # We simply call it and let it raise its exception on failure.
    schema.validate(config)


__all__ = [
    "RecursionContext",
    "RecursionDetector",
    "clear_recursion_context",
    "get_recursion_context",
    "validate_config",
    "with_recursion_detection",
]

# 🐍⛓️✅🪄
