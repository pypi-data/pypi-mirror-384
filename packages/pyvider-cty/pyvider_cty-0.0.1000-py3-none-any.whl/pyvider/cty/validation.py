# src/pyvider/cty/validation.py
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Any

from pyvider.cty.types import CtyType


def validate_config(schema: CtyType[Any], config: Any) -> None:
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


# 🐍⛓️🤔🪄
