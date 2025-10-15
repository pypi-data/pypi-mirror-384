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

import pytest
from unittest.mock import MagicMock, patch
from typer.testing import CliRunner

from snowflake.snowflake_data_validation.redshift.redshift_cli import redshift_app
from snowflake.snowflake_data_validation.configuration.singleton import Singleton


@pytest.fixture(autouse=True)
def singleton():
    """Clear singleton instances before each test."""
    Singleton._instances = {}


class TestRedshiftCLIRunAsyncValidation:
    """Unit tests for Redshift CLI run-async-validation command."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    @patch(
        "snowflake.snowflake_data_validation.redshift.redshift_cli._create_environment_from_config"
    )
    @patch(
        "snowflake.snowflake_data_validation.redshift.redshift_cli.ComparisonOrchestrator"
    )
    def test_run_async_validation_success(
        self,
        mock_orchestrator_class,
        mock_create_env,
    ):
        """Test successful async validation run - happy path."""
        # Create a temporary config file
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(
                """
source_platform: "Redshift"
target_platform: "Snowflake"
output_directory_path: "/tmp"
"""
            )
            temp_config_file = f.name

        try:
            mock_env = MagicMock()
            mock_create_env.return_value = mock_env

            mock_orchestrator = MagicMock()
            mock_orchestrator_class.from_validation_environment.return_value = (
                mock_orchestrator
            )

            result = self.runner.invoke(
                redshift_app,
                [
                    "run-async-validation",
                    "--data-validation-config-file",
                    temp_config_file,
                ],
            )

            assert result.exit_code == 0
            assert "Starting Redshift to Snowflake async validation..." in result.output
            assert "Validation completed successfully!" in result.output
            mock_create_env.assert_called_once()
            mock_orchestrator.run_async_comparison.assert_called_once()
        finally:
            # Clean up the temporary file
            os.unlink(temp_config_file)

    def test_run_async_validation_missing_config_file(self):
        """Test async validation with missing required config file parameter."""
        result = self.runner.invoke(redshift_app, ["run-async-validation"])

        assert result.exit_code != 0
        assert "Missing option" in result.output or "Usage:" in result.output

    @patch("pathlib.Path.exists")
    @patch(
        "snowflake.snowflake_data_validation.redshift.redshift_cli.ConfigurationLoader"
    )
    def test_run_async_validation_file_not_found_error(
        self, mock_config_loader, mock_path_exists
    ):
        """Test async validation with non-existent config file."""
        # Mock path exists to return False to trigger FileNotFoundError
        mock_path_exists.return_value = False
        mock_config_loader.side_effect = FileNotFoundError(
            "Configuration file not found in nonexistent.yaml"
        )

        result = self.runner.invoke(
            redshift_app,
            [
                "run-async-validation",
                "--data-validation-config-file",
                "nonexistent.yaml",
            ],
        )

        assert result.exit_code == 1
        assert "Configuration file not found" in result.output

    @patch(
        "snowflake.snowflake_data_validation.redshift.redshift_cli._create_environment_from_config"
    )
    def test_run_async_validation_connection_error(self, mock_create_env):
        """Test async validation with connection error."""
        # Create a temporary config file
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(
                """
source_platform: "Redshift"
target_platform: "Snowflake"
output_directory_path: "/tmp"
"""
            )
            temp_config_file = f.name

        try:
            # Mock _create_environment_from_config to raise ConnectionError
            mock_create_env.side_effect = ConnectionError("Database connection failed")

            result = self.runner.invoke(
                redshift_app,
                [
                    "run-async-validation",
                    "--data-validation-config-file",
                    temp_config_file,
                ],
            )

            assert result.exit_code == 1
            assert "Connection error" in result.output
        finally:
            # Clean up the temporary file
            os.unlink(temp_config_file)

    @patch("pathlib.Path.exists")
    @patch(
        "snowflake.snowflake_data_validation.redshift.redshift_cli.ConfigurationLoader"
    )
    @patch(
        "snowflake.snowflake_data_validation.redshift.redshift_cli.create_validation_environment_from_config"
    )
    def test_run_async_validation_generic_exception(
        self, mock_create_env, mock_config_loader, mock_path_exists
    ):
        """Test async validation with unexpected error."""
        # Mock path exists to return True
        mock_path_exists.return_value = True

        # Mock the configuration loader
        mock_config_model = MagicMock()
        mock_config_model.logging_configuration = (
            None  # No logging config to avoid MagicMock comparison
        )
        mock_config_loader.return_value.get_configuration_model.return_value = (
            mock_config_model
        )

        mock_create_env.side_effect = Exception("Unexpected error")

        result = self.runner.invoke(
            redshift_app,
            [
                "run-async-validation",
                "--data-validation-config-file",
                "test_config.yaml",
            ],
        )

        assert result.exit_code == 1
        assert "Operation failed" in result.output
