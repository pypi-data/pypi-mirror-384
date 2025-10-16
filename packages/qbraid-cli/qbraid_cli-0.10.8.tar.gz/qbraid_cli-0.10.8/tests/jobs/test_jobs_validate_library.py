# Copyright (c) 2024, qBraid Development Team
# All rights reserved.

"""
Unit tests for the validate_library function in the jobs.validation module.

"""

import pytest
import typer

from qbraid_cli.jobs.validation import validate_library


def test_validate_library_valid():
    """Test with a valid library name."""
    value = "braket"
    assert validate_library(value) == value, "Valid library should return the same name"


def test_validate_library_invalid():
    """Test with an invalid library name."""
    value = "nonexistentlib"
    with pytest.raises(typer.BadParameter) as exc_info:
        validate_library(value)
    assert "Library must be one of" in str(
        exc_info.value
    ), "Should raise BadParameter with message indicating allowed libraries"


def test_validate_library_case_insensitive():
    """Test with a valid library name in a different case."""
    value = "Braket"
    expected = "braket"
    assert validate_library(value) == expected, "Library validation should be case-insensitive"
