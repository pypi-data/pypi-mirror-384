# Copyright 2025 Pasteur Labs. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import os
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, FilePath

from tesseract_core.runtime.file_interactions import supported_format_type


class RuntimeConfig(BaseModel):
    """Available runtime configuration."""

    api_path: FilePath = Path("tesseract_api.py")
    name: str = "Tesseract"
    description: str = ""
    version: str = "unknown"
    debug: bool = False
    input_path: str = "."
    output_path: str = "."
    output_format: supported_format_type = "json"
    output_file: str = ""
    mlflow_tracking_uri: str = ""

    model_config = ConfigDict(frozen=True, extra="forbid")


def update_config(**kwargs: Any) -> None:
    """Create a new runtime configuration from the current environment.

    Passed keyword arguments will override environment variables.
    """
    global _current_config

    conf_settings = {}
    for field in RuntimeConfig.model_fields.keys():
        env_key = f"TESSERACT_{field.upper()}"
        if env_key in os.environ:
            conf_settings[field] = os.environ[env_key]

    for field in _config_overrides:
        conf_settings[field] = getattr(_current_config, field)

    conf_settings.update(kwargs)
    config = RuntimeConfig(**conf_settings)

    _config_overrides.update(set(conf_settings.keys()))
    _current_config = config


_current_config = None
_config_overrides = set()


def get_config() -> RuntimeConfig:
    """Return the current runtime configuration."""
    if _current_config is None:
        update_config()
    assert _current_config is not None
    return _current_config
