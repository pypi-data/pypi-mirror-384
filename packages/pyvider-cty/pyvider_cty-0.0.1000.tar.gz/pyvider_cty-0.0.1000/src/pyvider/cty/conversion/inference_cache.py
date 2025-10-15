# src/pyvider/cty/conversion/inference_cache.py
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from collections.abc import Callable, Generator
from contextlib import contextmanager
from functools import wraps
from typing import Any, TypeVar

from provide.foundation.utils import ContextScopedCache

from pyvider.cty.types import CtyType

"""Thread-safe, context-aware caching for type inference.

Provides isolated caches for recursive type inference operations,
ensuring performance and concurrent safety without memory leaks.
"""

F = TypeVar("F", bound=Callable[..., Any])

# Cache instances for type inference
_structural_key_cache = ContextScopedCache[int, tuple[Any, ...]]("structural_keys")
_container_schema_cache = ContextScopedCache[tuple[Any, ...], CtyType[Any]]("container_schemas")


def get_structural_key_cache() -> dict[int, tuple[Any, ...]] | None:
    """Get the current structural key cache from the context.

    Returns:
        Cache dictionary if in active context, None otherwise
    """
    if _structural_key_cache.is_active():
        # Access internal context var to maintain compatibility
        return _structural_key_cache._context_var.get()
    return None


def get_container_schema_cache() -> dict[tuple[Any, ...], CtyType[Any]] | None:
    """Get the current container schema cache from the context.

    Returns:
        Cache dictionary if in active context, None otherwise
    """
    if _container_schema_cache.is_active():
        # Access internal context var to maintain compatibility
        return _container_schema_cache._context_var.get()
    return None


@contextmanager
def inference_cache_context() -> Generator[None]:
    """Provide isolated inference caches for type inference operations.

    Creates scoped caches that are automatically cleaned up when exiting
    the context. Nested contexts reuse the parent cache. Respects the
    configuration setting for enabling/disabling caches.

    Yields:
        None (use get_*_cache() functions within context)

    Examples:
        >>> with inference_cache_context():
        ...     # Caches are active here
        ...     result = infer_cty_type_from_raw(data)
        ... # Caches automatically cleared
    """
    from pyvider.cty.config.runtime import CtyConfig

    config = CtyConfig.get_current()
    if not config.enable_type_inference_cache:
        yield
        return

    with _structural_key_cache.scope(), _container_schema_cache.scope():
        yield


def with_inference_cache(func: F) -> F:
    """Decorator providing isolated inference cache for function execution.

    Ensures thread/async safety by providing each invocation with its own
    cache context via ContextVar-based scoping.

    Args:
        func: Function to decorate

    Returns:
        Decorated function with cache context

    Examples:
        >>> @with_inference_cache
        ... def infer_type(value):
        ...     # Has access to inference caches
        ...     pass
    """

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        with inference_cache_context():
            return func(*args, **kwargs)

    return wrapper  # type: ignore[return-value]


# 🐍⛓️↔️🪄
