# src/pyvider/cty/validation/recursion.py
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""
Advanced recursion detection for CTY validation.

This module provides sophisticated recursion detection that can distinguish between:
1. Genuine circular references that would cause infinite loops
2. Normal nested data structures with repetitive patterns
3. Deep but finite nesting that should be allowed

The implementation is designed for production IaC requirements where:
- Complex configurations with deep nesting must be supported
- Genuine circular references must be prevented
- Performance must be predictable and measurable
- Debugging and monitoring capabilities are essential
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from functools import wraps
import threading
import time
from typing import Any

from provide.foundation import logger
from provide.foundation.errors import error_boundary

from pyvider.cty.config.defaults import (
    MAX_OBJECT_REVISITS,
    MAX_VALIDATION_DEPTH,
    MAX_VALIDATION_TIME_MS,
)


@dataclass
class ValidationNode:
    """Represents a node in the validation graph for cycle detection."""

    object_id: int
    object_type: str
    depth: int
    parent_path: str
    first_seen_at: float = field(default_factory=time.time)

    def __post_init__(self) -> None:
        self.visits = 1


@dataclass
class RecursionContext:
    """Thread-local context for tracking validation recursion."""

    # Object identity tracking for cycle detection
    validation_graph: dict[int, ValidationNode] = field(default_factory=dict)

    # Path tracking for detailed diagnostics
    validation_path: list[str] = field(default_factory=list)

    # Performance monitoring
    max_depth_reached: int = 0
    total_validations: int = 0
    validation_start_time: float = field(default_factory=time.time)

    # Configuration thresholds
    max_depth_allowed: int = MAX_VALIDATION_DEPTH
    max_object_revisits: int = MAX_OBJECT_REVISITS
    max_validation_time_ms: int = MAX_VALIDATION_TIME_MS

    def reset(self) -> None:
        """Reset context for new validation session."""
        self.validation_graph.clear()
        self.validation_path.clear()
        self.max_depth_reached = 0
        self.total_validations = 0
        self.validation_start_time = time.time()


# Thread-local storage for recursion contexts
_thread_local = threading.local()


def get_recursion_context() -> RecursionContext:
    """Get or create thread-local recursion context."""
    if not hasattr(_thread_local, "recursion_context"):
        _thread_local.recursion_context = RecursionContext()
    return _thread_local.recursion_context


def clear_recursion_context() -> None:
    """Clear thread-local recursion context."""
    if hasattr(_thread_local, "recursion_context"):
        _thread_local.recursion_context.reset()


class RecursionDetector:
    """
    Advanced recursion detector for CTY validation.

    This detector uses sophisticated algorithms to distinguish between:
    - Circular references (object A -> object B -> object A)
    - Deep but finite nesting (legitimate complex configurations)
    - Performance pathological cases (excessive validation time)
    """

    def __init__(self, context: RecursionContext | None = None) -> None:
        self.context = context or get_recursion_context()

    def should_continue_validation(self, value: Any, current_path: str = "") -> tuple[bool, str | None]:
        """
        Determine if validation should continue for the given value.

        Returns:
            (should_continue, reason_if_stopped)

        Production requirements:
        - Must handle legitimate deep nesting (1000+ levels)
        - Must detect genuine circular references quickly
        - Must provide detailed diagnostics for debugging
        - Must have predictable performance characteristics
        """

        # Performance safeguards - prevent pathological cases
        elapsed_ms = (time.time() - self.context.validation_start_time) * 1000
        if elapsed_ms > self.context.max_validation_time_ms:
            reason = (
                f"Validation timeout after {elapsed_ms:.1f}ms (max: {self.context.max_validation_time_ms}ms)"
            )
            logger.warning(
                "CTY validation timeout exceeded",
                elapsed_ms=elapsed_ms,
                max_allowed_ms=self.context.max_validation_time_ms,
                path=current_path,
                trace="advanced_recursion_detection",
            )
            return False, reason

        # Update context
        self.context.total_validations += 1
        current_depth = len(self.context.validation_path)
        self.context.max_depth_reached = max(self.context.max_depth_reached, current_depth)

        # Depth safeguards - only trigger for truly deep recursion
        if current_depth > self.context.max_depth_allowed:
            reason = f"Maximum nesting depth exceeded: {current_depth} > {self.context.max_depth_allowed}"
            logger.warning(
                "CTY validation depth limit exceeded",
                current_depth=current_depth,
                max_allowed=self.context.max_depth_allowed,
                path=current_path,
                trace="advanced_recursion_detection",
            )
            return False, reason

        # Skip cycle detection for primitive types and simple collections (performance optimization)
        if isinstance(value, (str, int, float, bool, type(None))):
            return True, None

        # Skip cycle detection for simple lists of primitives
        if isinstance(value, list) and all(
            isinstance(item, (str, int, float, bool, type(None))) for item in value
        ):
            return True, None

        # Sophisticated cycle detection
        value_id = id(value)
        value_type = type(value).__name__

        if value_id in self.context.validation_graph:
            node = self.context.validation_graph[value_id]
            node.visits += 1

            # Allow some revisits for complex but legitimate schemas
            if node.visits > self.context.max_object_revisits:
                reason = (
                    f"Circular reference detected: {value_type} object visited "
                    f"{node.visits} times (max: {self.context.max_object_revisits})"
                )
                logger.debug(
                    "CTY circular reference detected",
                    object_type=value_type,
                    object_id=value_id,
                    visits=node.visits,
                    first_seen_depth=node.depth,
                    current_depth=current_depth,
                    path=current_path,
                    trace="advanced_recursion_detection",
                )
                return False, reason

            # Log revisit for monitoring
            logger.debug(
                "CTY object revisited",
                object_type=value_type,
                object_id=value_id,
                visits=node.visits,
                path=current_path,
                trace="advanced_recursion_detection",
            )
        else:
            # First time seeing this object
            self.context.validation_graph[value_id] = ValidationNode(
                object_id=value_id,
                object_type=value_type,
                depth=current_depth,
                parent_path=current_path,
            )

        return True, None

    def enter_validation_scope(self, scope_name: str) -> None:
        """Enter a new validation scope for path tracking."""
        self.context.validation_path.append(scope_name)

    def exit_validation_scope(self) -> None:
        """Exit the current validation scope."""
        if self.context.validation_path:
            self.context.validation_path.pop()

    def get_current_path(self) -> str:
        """Get the current validation path for diagnostics."""
        return " -> ".join(self.context.validation_path)

    def get_performance_metrics(self) -> dict[str, Any]:
        """Get performance metrics for monitoring and debugging."""
        elapsed_ms = (time.time() - self.context.validation_start_time) * 1000
        return {
            "total_validations": self.context.total_validations,
            "max_depth_reached": self.context.max_depth_reached,
            "elapsed_ms": elapsed_ms,
            "objects_in_graph": len(self.context.validation_graph),
            "avg_validations_per_ms": self.context.total_validations / max(elapsed_ms, 0.001),
            "current_path": self.get_current_path(),
        }


def with_recursion_detection(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator for advanced recursion detection in validation functions.
    """

    @wraps(func)
    def wrapper(self: Any, value: Any, *args: Any, **kwargs: Any) -> Any:
        context = get_recursion_context()
        # A call is top-level if the context has not been used yet.
        is_top_level_call = context.total_validations == 0
        if is_top_level_call:
            context.reset()

        detector = RecursionDetector(context)
        scope_name = f"{self.__class__.__name__}.validate(type={type(value).__name__})"

        with error_boundary(
            context={
                "operation": "recursion_detection",
                "type_name": self.__class__.__name__,
                "value_type": type(value).__name__,
                "validation_depth": len(context.validation_path),
                "total_validations": context.total_validations,
            }
        ):
            detector.enter_validation_scope(scope_name)

            try:
                should_continue, reason = detector.should_continue_validation(
                    value, detector.get_current_path()
                )
                if not should_continue:
                    from pyvider.cty.values import CtyValue

                    logger.warning(
                        "CTY validation stopped due to recursion detection",
                        reason=reason,
                        value_type=type(value).__name__,
                        path=detector.get_current_path(),
                    )
                    return CtyValue.unknown(self)

                # The decorator no longer passes the internal flag down.
                return func(self, value, *args, **kwargs)
            finally:
                detector.exit_validation_scope()
                # The context is now only cleared by the top-level caller (e.g., test setup),
                # not by the decorator.
                if is_top_level_call:
                    pass

    return wrapper


# 🐍⛓️✅🪄
