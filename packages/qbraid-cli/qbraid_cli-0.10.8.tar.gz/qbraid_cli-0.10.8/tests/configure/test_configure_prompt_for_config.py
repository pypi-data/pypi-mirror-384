# Copyright (c) 2024, qBraid Development Team
# All rights reserved.

"""
Unit tests for the prompt_for_config function in the configure app.

"""

import configparser
from unittest.mock import patch

from qbraid_cli.configure.actions import prompt_for_config


def test_enter_new_values():
    """Test prompt_for_config when the user enters new values for multiple settings."""
    config = configparser.ConfigParser()
    config.add_section("Settings")

    # Initial values
    settings = [
        ("url", "http://example.com", "http://newexample.com"),
    ]

    # Setup config with initial values
    for key, initial_value, _ in settings:
        config.set("Settings", key, initial_value)

    # Test each setting one by one
    results = {}
    for key, _, new_value in settings:
        with patch("typer.prompt", return_value=new_value):
            results[key] = prompt_for_config(config, "Settings", key)

    # Verify the results
    for key, _, new_value in settings:
        assert results[key] == new_value, f"Should return the new value for {key}"


def test_new_value_validation():
    """Test prompt_for_config when the user enters a new value that needs to be validated."""
    config = configparser.ConfigParser()
    config.add_section("Settings")
    config.set("Settings", "email", "user@example.com")
    new_email = "newuser@example.com"
    with (
        patch("typer.prompt", return_value=new_email),
        patch(
            "qbraid_cli.configure.actions.validate_input", return_value=new_email
        ) as mock_validate,
    ):
        result = prompt_for_config(config, "Settings", "email")
    mock_validate.assert_called_once_with("email", new_email)
    assert result == new_email, "Should return the new validated email"
