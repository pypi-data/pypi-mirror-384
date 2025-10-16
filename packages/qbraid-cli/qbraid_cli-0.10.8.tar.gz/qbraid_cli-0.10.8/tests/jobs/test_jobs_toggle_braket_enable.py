# Copyright (c) 2024, qBraid Development Team
# All rights reserved.

"""
Unit tests for the enable_braket function in the toggle_braket module.

"""

import subprocess
from unittest.mock import call, patch

import pytest
import typer

from qbraid_cli.jobs.toggle_braket import enable_braket, fetch_botocore_version


def test_helper_function_invocations():
    """Test that `enable_braket` correctly calls its helper functions."""
    with (
        patch(
            "qbraid_cli.jobs.toggle_braket.get_package_data",
            return_value=("1.0.0", "1.2.0", "/some/path", "/usr/bin/python"),
        ) as mock_get_package_data,
        patch("qbraid_cli.jobs.toggle_braket.confirm_updates") as mock_confirm_updates,
        patch("qbraid_cli.jobs.toggle_braket.aws_configure_dummy") as mock_aws_configure_dummy,
    ):
        with patch("subprocess.check_call"):
            enable_braket()

        mock_get_package_data.assert_called_once_with("boto3")
        mock_confirm_updates.assert_called()
        mock_aws_configure_dummy.assert_called_once()


def test_subprocess_calls():
    """Test the subprocess calls within `enable_braket`."""
    mock_python_path = "/usr/bin/python"

    version = fetch_botocore_version()

    with (
        patch(
            "qbraid_cli.jobs.toggle_braket.get_package_data",
            return_value=("1.0.0", version, "/some/path", mock_python_path),
        ),
        patch("qbraid_cli.jobs.toggle_braket.confirm_updates"),
        patch("qbraid_cli.jobs.toggle_braket.aws_configure_dummy"),
        patch("subprocess.check_call") as mock_check_call,
    ):
        enable_braket()

        # Expected subprocess calls in order
        expected_calls = [
            call([mock_python_path, "-m", "pip", "install", f"boto3=={version}"]),
            call([mock_python_path, "-m", "pip", "uninstall", "botocore", "-y", "--quiet"]),
            call(
                [
                    mock_python_path,
                    "-m",
                    "pip",
                    "install",
                    "git+https://github.com/qBraid/botocore.git",
                ]
            ),
        ]
        mock_check_call.assert_has_calls(expected_calls, any_order=False)


def test_subprocess_error_handling():
    """ "Test if the program exits correctly using typer.Exit"""
    with (
        patch(
            "qbraid_cli.jobs.toggle_braket.get_package_data",
            return_value=("1.0.0", "1.2.0", "/some/path", "/usr/bin/python"),
        ),
        patch("qbraid_cli.jobs.toggle_braket.confirm_updates"),
        patch("qbraid_cli.jobs.toggle_braket.aws_configure_dummy"),
        patch(
            "subprocess.check_call",
            side_effect=subprocess.CalledProcessError(returncode=1, cmd="cmd"),
        ),
    ):
        with pytest.raises(typer.Exit):
            enable_braket()


def test_success_feedback():
    """Test feedback for successful execution"""
    with (
        patch(
            "qbraid_cli.jobs.toggle_braket.get_package_data",
            return_value=("1.0.0", "1.2.0", "/some/path", "/usr/bin/python"),
        ),
        patch("qbraid_cli.jobs.toggle_braket.confirm_updates"),
        patch("qbraid_cli.jobs.toggle_braket.aws_configure_dummy"),
        patch("subprocess.check_call"),
        patch("typer.secho") as mock_secho,
    ):
        enable_braket()

        # Verify success messages
        success_message_calls = [
            call("\nSuccessfully enabled qBraid quantum jobs.", fg=typer.colors.GREEN, bold=True),
            call("\nTo disable, run: \n\n\t$ qbraid jobs disable braket\n"),
        ]
        mock_secho.assert_has_calls(success_message_calls, any_order=False)
