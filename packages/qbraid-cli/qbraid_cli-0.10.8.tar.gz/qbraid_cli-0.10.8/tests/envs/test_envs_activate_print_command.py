# Copyright (c) 2024, qBraid Development Team
# All rights reserved.

"""
Unit tests for the print_activate_command function in the envs app.

"""

import os
from unittest.mock import patch

import pytest
import typer

from qbraid_cli.envs.activate import print_activate_command


def test_print_activate_command(tmp_path, capsys):
    """
    Test that the activate command is correctly printed for both Unix-like and Windows systems,
    depending on the operating system.
    """
    if os.name == "posix":
        os_name_to_patch = "posix"
        expected_output = (
            f"To activate this environment, use command:\n\n\t$ source {tmp_path}/bin/activate\n\n"
        )
    else:
        os_name_to_patch = "nt"
        expected_output = (
            f"To activate this environment, use command:\n\n\t$ {tmp_path}\\Scripts\\activate\n\n"
            f"Or for PowerShell, use:\n\n\t$ & {tmp_path}\\Scripts\\Activate.ps1\n\n"
        )

    with patch.object(os, "name", os_name_to_patch), pytest.raises(typer.Exit):
        print_activate_command(tmp_path)
    captured = capsys.readouterr()
    assert captured.out == expected_output
