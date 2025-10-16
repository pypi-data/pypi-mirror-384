# Copyright (c) 2024, qBraid Development Team
# All rights reserved.

"""
Unit tests for the disable_braket function in the toggle_braket module.

"""

import subprocess
from unittest.mock import patch

import pytest
import typer

from qbraid_cli.jobs.toggle_braket import disable_braket


def test_helper_functions_invoked_correctly():
    """
    Tests that `get_package_data` and `confirm_updates` helper functions are called with
    the correct arguments when `disable_braket` is executed.
    """
    with (
        patch(
            "qbraid_cli.jobs.toggle_braket.get_package_data",
            return_value=("1.0.0", "1.1.0", "/some/path", "/usr/bin/python"),
        ) as mock_get_package_data_disable,
        patch("qbraid_cli.jobs.toggle_braket.confirm_updates") as mock_confirm_updates,
    ):
        # Assume successful subprocess call
        with patch("subprocess.check_call"):
            disable_braket()

        mock_get_package_data_disable.assert_called_once_with("botocore")
        mock_confirm_updates.assert_called_once_with("disable", "/some/path")


def test_package_version_specification_for_reinstallation():
    """
    Tests that the correct package version is specified for reinstallation during the
    `disable_braket` function execution.
    """
    with (
        patch(
            "qbraid_cli.jobs.toggle_braket.get_package_data",
            return_value=("1.0.0", "1.1.0", "/some/path", "/usr/bin/python"),
        ),
        patch("qbraid_cli.jobs.toggle_braket.confirm_updates"),
        patch("subprocess.check_call") as mock_check_call,
    ):
        disable_braket()

        mock_check_call.assert_called_with(
            [
                "/usr/bin/python",
                "-m",
                "pip",
                "install",
                "botocore~=1.0.0",  # The version is specified because installed < latest
                "--force-reinstall",
            ],
            stderr=subprocess.DEVNULL,
        )


def test_subprocess_execution_and_error_handling():
    """
    Tests if `disable_braket` correctly handles subprocess execution for package reinstallation
    and raises the typer.Exit when a subprocess call fails.
    """
    with (
        patch(
            "qbraid_cli.jobs.toggle_braket.get_package_data",
            return_value=("1.0.0", "1.0.0", "/some/path", "/usr/bin/python"),
        ),
        patch("qbraid_cli.jobs.toggle_braket.confirm_updates"),
        patch("subprocess.check_call", side_effect=subprocess.CalledProcessError(1, "cmd")),
        patch("qbraid_cli.handlers.handle_error"),
    ):
        with pytest.raises(typer.Exit):
            disable_braket()


def test_success_message_displayed():
    """Tests if correct success messages are displayed to the user."""
    with (
        patch(
            "qbraid_cli.jobs.toggle_braket.get_package_data",
            return_value=("1.0.0", "1.0.0", "/some/path", "/usr/bin/python"),
        ),
        patch("qbraid_cli.jobs.toggle_braket.confirm_updates"),
        patch("subprocess.check_call"),
        patch("typer.secho") as mock_secho,
    ):
        disable_braket()

        mock_secho.assert_any_call(
            "\nSuccessfully disabled qBraid quantum jobs.", fg=typer.colors.GREEN, bold=True
        )
        mock_secho.assert_any_call("\nTo enable, run: \n\n\t$ qbraid jobs enable braket\n")
