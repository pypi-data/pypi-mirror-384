# src/pyvider/cty/context/validation_context.py
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

# In a new file: pyvider/cty/context/validation_context.py
from collections.abc import Generator
from contextlib import contextmanager
import contextvars

MAX_VALIDATION_DEPTH = 500  # Configurable

_validation_depth = contextvars.ContextVar("validation_depth", default=0)


@contextmanager
def deeper_validation() -> Generator[None]:
    """A context manager to safely increment and decrement validation depth."""
    token = _validation_depth.set(_validation_depth.get() + 1)
    try:
        yield
    finally:
        _validation_depth.reset(token)


def get_validation_depth() -> int:
    """Returns the current validation depth."""
    return _validation_depth.get()


# 🐍⛓️🏷️🪄
