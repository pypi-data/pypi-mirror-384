# Copyright (c) 2024, qBraid Development Team
# All rights reserved.

"""
Unit tests for the `qbraid_cli.envs.app` module, specifically for the `envs list` command.

"""

from pathlib import Path
from unittest.mock import patch

import typer.testing

from qbraid_cli.envs import envs_app


@patch("qbraid_cli.envs.app.installed_envs_data", return_value=({}, {}))
def test_envs_list_no_installed(mock_installed_envs_data):
    """Test listing environments when no environments are installed."""
    runner = typer.testing.CliRunner()
    result = runner.invoke(envs_app, ["list"])
    mock_installed_envs_data.assert_called_once()
    assert "No qBraid environments installed." in result.stdout


@patch("qbraid_cli.envs.app.installed_envs_data")
def test_envs_list_with_installed(mock_installed_envs_data):
    """Test listing environments when environments are installed."""
    test_env_path = Path("/path/to/test-env")

    mock_installed_envs_data.return_value = (
        {"test_slug": test_env_path},
        {"TestEnv": "test_slug"},
    )
    runner = typer.testing.CliRunner()
    result = runner.invoke(envs_app, ["list"])
    assert "TestEnv" in result.stdout and str(test_env_path) in result.stdout
