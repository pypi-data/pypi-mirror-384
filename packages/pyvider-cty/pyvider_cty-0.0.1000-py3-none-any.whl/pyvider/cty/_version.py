# src/pyvider/cty/_version.py
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from provide.foundation.utils.versioning import get_version

"""Version handling for pyvider-cty.

This module uses the shared versioning utility from provide-foundation.
"""

__version__ = get_version("pyvider-cty", caller_file=__file__)

__all__ = ["__version__"]

# 🐍⛓️🤔🪄
