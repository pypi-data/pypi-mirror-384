# Copyright (c) 2024, qBraid Development Team
# All rights reserved.

"""
Unit tests for the find_shell_rc function in the activate app.

"""

from pathlib import Path

import pytest

from qbraid_cli.envs.activate import (
    find_shell_rc,  # Adjust the import according to your module structure
)


def test_find_shell_rc_supported_shell(tmp_path, monkeypatch):
    """
    Test that find_shell_rc returns the path to an existing shell configuration file.
    """
    # Setup: Create a fake home directory with a .bashrc file
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    (fake_home / ".bashrc").touch()

    # Use monkeypatch to simulate the home directory
    monkeypatch.setattr(Path, "home", lambda: fake_home)
    # Test
    expected = str(fake_home / ".bashrc")
    assert find_shell_rc("bash") == expected, "Should return the path to .bashrc"


def test_find_shell_rc_unsupported_shell():
    """
    Test that find_shell_rc raises ValueError for unsupported shells.
    """
    with pytest.raises(ValueError):
        find_shell_rc("fish")


def test_find_shell_rc_no_config_file(tmp_path, monkeypatch):
    """
    Test that find_shell_rc raises FileNotFoundError when no config file is found.
    """
    # Setup: Create a fake home directory without any bash config files
    fake_home = tmp_path / "home"
    fake_home.mkdir()

    # Use monkeypatch to simulate the home directory
    monkeypatch.setattr(Path, "home", lambda: fake_home)

    with pytest.raises(FileNotFoundError):
        find_shell_rc("bash")
