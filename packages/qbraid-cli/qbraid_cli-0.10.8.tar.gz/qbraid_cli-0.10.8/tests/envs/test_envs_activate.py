# Copyright (c) 2024, qBraid Development Team
# All rights reserved.

"""
Unit tests for the `qbraid_cli.envs.app` module's `activate` command.

"""

from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from qbraid_cli.envs.app import envs_app

runner = CliRunner()


@patch("qbraid_cli.envs.activate.activate_pyvenv")
@patch("qbraid_cli.envs.app.installed_envs_data")
def test_envs_activate_existing_env(mock_installed_envs_data, mock_activate_pyvenv):
    """Test activating an existing environment."""
    # Setup mock return values to simulate existing environments
    mock_installed_envs_data.return_value = (
        {"env1": Path("/path/to/env1"), "env2": Path("/path/to/env2")},
        {"alias1": "env1"},
    )
    runner.invoke(envs_app, ["list"])
    runner.invoke(envs_app, ["activate", "alias1"])
    mock_activate_pyvenv.assert_called_once_with(Path("/path/to/env1/pyenv"))


@patch("qbraid_cli.envs.app.installed_envs_data")
def test_envs_activate_nonexistent_env(mock_installed_envs_data):
    """Test activating a nonexistent environment."""
    mock_installed_envs_data.return_value = (
        {"env1": Path("/path/to/env1")},  # Only env1 exists
        {"alias1": "env1"},
    )

    result = runner.invoke(envs_app, ["activate", "nonexistent"])
    assert result.exit_code == 2, "Expected exit code 2 for a bad parameter"
