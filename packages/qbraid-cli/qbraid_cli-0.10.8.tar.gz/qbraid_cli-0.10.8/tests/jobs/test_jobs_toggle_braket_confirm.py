# Copyright (c) 2024, qBraid Development Team
# All rights reserved.

"""
Unit tests for the confirm_updates function in the toggle_braket module.

"""

from unittest.mock import patch

import pytest
import typer

from qbraid_cli.jobs.toggle_braket import confirm_updates


@pytest.mark.parametrize("mode", ["enable", "disable"])
def test_valid_mode_no_versions_provided(mode):
    """
    Verify that the function processes "enable" and
    "disable" modes correctly without raising an exception.
    """
    with patch("typer.echo") as mock_echo, patch("typer.confirm", return_value=True):
        confirm_updates(mode, "/fake/site-packages")
        mock_echo.assert_called()


def test_invalid_mode_raises_value_error():
    """test that providing an invalid mode raises a ValueError."""
    with pytest.raises(ValueError) as exc_info:
        confirm_updates("invalid", "/fake/site-packages")
    assert "Invalid mode" in str(exc_info.value)


@pytest.mark.parametrize("user_confirmation", [True, False])
def test_user_confirmation_behavior(user_confirmation):
    """Test that the function proceeds without raising an exception when the user confirms"""
    with patch("typer.echo"), patch("typer.confirm", return_value=user_confirmation):
        if not user_confirmation:
            with pytest.raises(typer.Exit):
                confirm_updates("enable", "/fake/site-packages")
        else:
            confirm_updates("enable", "/fake/site-packages")


def test_version_warning():
    """Check that function can distinguish between versions."""
    installed_version = "1.0.0"
    latest_version = "1.2.0"
    with patch("typer.echo") as mock_echo, patch("typer.confirm", return_value=True):
        confirm_updates("enable", "/fake/site-packages", installed_version, latest_version)
        mock_echo.assert_any_call("==> WARNING: A different version of boto3 is required. <==")
