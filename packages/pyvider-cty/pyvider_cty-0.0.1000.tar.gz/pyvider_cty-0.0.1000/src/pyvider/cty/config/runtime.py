# src/pyvider/cty/config/runtime.py
# SPDX-FileCopyrightText: Copyright (c) provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Self

from attrs import define
from provide.foundation.config import RuntimeConfig, env_field

from pyvider.cty.config.defaults import ENABLE_TYPE_INFERENCE_CACHE

"""Runtime configuration for pyvider-cty using Foundation config patterns."""


@define
class CtyConfig(RuntimeConfig):
    """Runtime configuration for pyvider-cty.

    Uses Foundation's RuntimeConfig for consistent environment variable loading
    and validation patterns.
    """

    enable_type_inference_cache: bool = env_field(
        env_var="PYVIDER_CTY_ENABLE_TYPE_INFERENCE_CACHE",
        default=ENABLE_TYPE_INFERENCE_CACHE,
    )

    @classmethod
    def get_current(cls) -> Self:
        """Get current configuration from environment variables.

        Returns:
            Current CtyConfig instance loaded from environment
        """
        return cls.from_env(prefix="PYVIDER_CTY")


# 🐍⛓️⚙️🪄
