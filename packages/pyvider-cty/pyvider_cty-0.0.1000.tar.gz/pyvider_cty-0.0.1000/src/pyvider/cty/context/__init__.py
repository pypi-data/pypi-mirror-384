# src/pyvider/cty/context/__init__.py
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from pyvider.cty.context.validation_context import (
    MAX_VALIDATION_DEPTH,
    deeper_validation,
    get_validation_depth,
)

# pyvider/cty/context/__init__.py
"""
Provides context management for CTY operations.

This package includes tools for managing and retrieving the current operational
context within the CTY system, which can influence how types and values are
processed or validated.
"""

__all__ = [
    "MAX_VALIDATION_DEPTH",
    "deeper_validation",
    "get_validation_depth",
]

# 🐍⛓️🏷️🪄
