# Copyright (c) 2024, qBraid Development Team
# All rights reserved.

"""
Unit tests for the validate_input function in the configure app.

"""

import pytest
import typer

from qbraid_cli.configure.actions import validate_input


@pytest.mark.parametrize(
    "key,value",
    [
        ("url", "http://example.com"),
        ("url", "https://example.com"),
        ("email", "user@example.com"),
        ("api-key", "a1B2c3D4e5F"),
    ],
)
def test_validate_input_valid(key, value):
    """Test validate_input with valid inputs."""
    assert validate_input(key, value) == value, f"Valid {key} should not raise an exception"


@pytest.mark.parametrize(
    "key,value,expected",
    [
        ("api-key", "a1B2c3D4e5F\r", "a1B2c3D4e5F"),
    ],
)
def test_validate_input_valid_strip(key, value, expected):
    """Test validate_input with valid inputs."""
    assert validate_input(key, value) == expected, f"Valid {key} should not raise an exception"


@pytest.mark.parametrize(
    "key,value,exception_message",
    [
        ("url", "htt://example.com", "Invalid URL format."),
        ("url", "example.com", "Invalid URL format."),
        ("email", "user@example", "Invalid email format."),
        ("email", "userexample.com", "Invalid email format."),
        ("api-key", "@#$1234567890", "Invalid API key format."),
        ("api-key", "a1B2c3D4e5F6g^74()", "Invalid API key format."),
    ],
)
def test_validate_input_invalid(key, value, exception_message):
    """Test validate_input with invalid inputs."""
    with pytest.raises(typer.BadParameter) as exc_info:
        validate_input(key, value)
    assert (
        str(exc_info.value) == exception_message
    ), f"{key} validation should raise the correct exception message"


def test_validate_input_unexpected_key():
    """Test validate_input with an unexpected key."""
    key = "unexpected-key"
    value = "anyvalue"
    # Assuming the function simply returns the value for unexpected keys
    assert validate_input(key, value) == value, "Unexpected key should not alter the value"
