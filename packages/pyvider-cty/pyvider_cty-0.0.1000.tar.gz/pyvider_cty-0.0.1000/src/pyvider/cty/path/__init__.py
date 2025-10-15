# src/pyvider/cty/path/__init__.py
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from pyvider.cty.path.base import (
    CtyPath,
    GetAttrStep,
    IndexStep,
    KeyStep,
    PathStep,
)

#
# pyvider/cty/path/__init__.py
#
"""
Provides CTY path navigation capabilities.

This package defines classes and utilities for constructing and applying
paths to navigate through nested CTY data structures (objects, lists, maps, tuples),
similar to property accessors or indexers in other languages.
"""

__all__ = [
    "CtyPath",
    "GetAttrStep",
    "IndexStep",
    "KeyStep",
    "PathStep",
]

# 🐍🏗️🐣

# 🐍⛓️➡️🪄
