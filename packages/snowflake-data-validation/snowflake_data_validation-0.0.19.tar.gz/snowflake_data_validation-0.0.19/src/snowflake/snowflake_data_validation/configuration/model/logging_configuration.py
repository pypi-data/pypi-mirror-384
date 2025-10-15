# Copyright 2025 Snowflake Inc.
# SPDX-License-Identifier: Apache-2.0
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Logging configuration model for Snowflake Data Validation."""

import logging

from pydantic import BaseModel, field_validator


class LoggingConfiguration(BaseModel):
    """Logging configuration model.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        console_level: Console logging level (defaults to level if not specified)
        file_level: File logging level (defaults to level if not specified)

    """

    level: str = "INFO"
    console_level: str | None = None
    file_level: str | None = None

    @field_validator("level", "console_level", "file_level")
    @classmethod
    def validate_log_level(cls, value: str | None) -> str | None:
        """Validate logging level values."""
        if value is None:
            return value

        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if value.upper() not in valid_levels:
            raise ValueError(
                f"Invalid logging level: {value}. "
                f"Valid levels are: {', '.join(valid_levels)}"
            )
        return value.upper()

    def get_console_level(self) -> str:
        """Get the console logging level."""
        return self.console_level or self.level

    def get_file_level(self) -> str:
        """Get the file logging level."""
        return self.file_level or self.level

    def get_console_level_int(self) -> int:
        """Get the console logging level as integer."""
        return getattr(logging, self.get_console_level())

    def get_file_level_int(self) -> int:
        """Get the file logging level as integer."""
        return getattr(logging, self.get_file_level())
