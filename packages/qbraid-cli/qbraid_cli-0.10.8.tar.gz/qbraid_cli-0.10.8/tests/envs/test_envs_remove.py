# Copyright (c) 2024, qBraid Development Team
# All rights reserved.

"""
Unit tests for the `qbraid envs remove` command.

"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import typer.testing

from qbraid_cli.envs import envs_app

runner = typer.testing.CliRunner()


@patch("shutil.rmtree", MagicMock())
def test_envs_remove():
    """Test removing an environment."""
    test_env_path = Path("/path/to/env")
    with (
        patch(
            "qbraid_cli.envs.app.installed_envs_data",
            return_value=({"test-slug": test_env_path}, {"Test Env": "test-slug"}),
        ),
    ):
        name = "Test Env"
        result = runner.invoke(envs_app, ["remove", "--name", name], input="y\n")
    assert (
        f"Warning: You are about to delete the environment 'Test Env' located at '{test_env_path}'"
        in result.stdout
    )
