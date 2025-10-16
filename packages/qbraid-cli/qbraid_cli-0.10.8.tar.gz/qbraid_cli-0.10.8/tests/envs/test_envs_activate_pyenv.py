# Copyright (c) 2024, qBraid Development Team
# All rights reserved.

"""
Unit tests for the activate_pyvenv function in the activate module.

"""

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from qbraid_cli.envs.activate import activate_pyvenv


def test_activate_pyvenv_with_no_shell():
    """Test activating venv when SHELL environment variable is not set."""
    venv_path = Path("/fake/path")
    with (
        patch.dict(os.environ, {}, clear=True),
        patch("qbraid_cli.envs.activate.print_activate_command") as mock_print_command,
    ):
        activate_pyvenv(venv_path)
        mock_print_command.assert_called_once_with(venv_path)


def test_activate_pyvenv_with_exceptions():
    """Test handling when find_shell_rc raises exceptions."""
    venv_path = Path("/fake/path")
    with (
        patch.dict(os.environ, {"SHELL": "/bin/bash"}),
        patch("qbraid_cli.envs.activate.find_shell_rc", side_effect=FileNotFoundError()),
        patch("qbraid_cli.envs.activate.print_activate_command") as mock_print_command,
    ):
        activate_pyvenv(venv_path)
        mock_print_command.assert_called_once()


@pytest.mark.skipif(os.name == "nt", reason="Test only works for Unix-like operating systems")
def test_activate_pyvenv_success():
    """Test successful venv activation command construction."""
    venv_path = Path("/fake/venv")
    fake_shell_rc = "/fake/home/.bashrc"
    with (
        patch.dict(os.environ, {"SHELL": "/bin/bash"}),
        patch("qbraid_cli.envs.activate.find_shell_rc", return_value=fake_shell_rc),
        patch("os.system") as mock_os_system,
    ):
        activate_pyvenv(venv_path)
        expected_command = (
            f"cat {fake_shell_rc} {venv_path}/bin/activate > "
            f"{venv_path}/bin/activate2 && /bin/bash --rcfile "
            f"{venv_path}/bin/activate2"
        )
        mock_os_system.assert_called_with(expected_command)


def test_activate_pyvenv_fail():
    """Test unsuccessful venv activation command construction."""
    venv_path = Path("/fake/venv")
    shell_path = "C:\\Windows\\System32\\cmd.exe"
    with (
        patch.dict("os.environ", {"SHELL": shell_path}),
        patch("qbraid_cli.envs.activate.find_shell_rc", side_effect=FileNotFoundError()),
        patch("qbraid_cli.envs.activate.print_activate_command") as mock_print_activate_command,
    ):
        activate_pyvenv(venv_path)
        mock_print_activate_command.assert_called_once_with(venv_path)
