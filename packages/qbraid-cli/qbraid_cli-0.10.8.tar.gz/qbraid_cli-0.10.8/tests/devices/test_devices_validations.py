# Copyright (c) 2024, qBraid Development Team
# All rights reserved.

"""
Unit tests for the validation functions in the devices app.

"""

import pytest
import typer

from qbraid_cli.devices.validation import validate_provider, validate_status, validate_type


@pytest.mark.parametrize(
    "value, expected",
    [
        ("ONLINE", "ONLINE"),
        ("offline", "OFFLINE"),  # Test case insensitivity
        ("RetIred", "RETIRED"),
        (None, None),  # Check handling of None
    ],
)
def test_validate_status_success(value, expected):
    """Test validate_status with valid inputs."""
    assert validate_status(value) == expected


def test_validate_status_failure():
    """Test validate_status with invalid inputs."""
    with pytest.raises(typer.BadParameter):
        validate_status("INVALID_STATUS")


@pytest.mark.parametrize(
    "value, expected",
    [
        ("QPU", "QPU"),
        ("simulAtor", "SIMULATOR"),  # Test case insensitivity
        (None, None),  # Check handling of None
    ],
)
def test_validate_type_success(value, expected):
    """Test validate_type with valid inputs."""
    assert validate_type(value) == expected


def test_validate_type_failure():
    """Test validate_type with invalid inputs."""
    with pytest.raises(typer.BadParameter):
        validate_type("INVALID_TYPE")


@pytest.mark.parametrize(
    "value, expected",
    [
        ("AWS", "AWS"),  #
        ("ibm", "IBM"),
        ("IonQ", "IonQ"),
        ("rigeTTi", "Rigetti"),  # Test case insensitivity
        (None, None),  # Check handling of None
    ],
)
def test_validate_provider_success(value, expected):
    """Test validate_provider with valid inputs."""
    assert validate_provider(value) == expected


def test_validate_provider_failure():
    """Test validate_provider with invalid inputs."""
    with pytest.raises(typer.BadParameter):
        validate_provider("INVALID_PROVIDER")
