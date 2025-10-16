# Copyright (c) 2024, qBraid Development Team
# All rights reserved.

"""
Unit tests for the `qbraid_cli.admin.app` module's `headers` command.

"""
import datetime
import os
import re

import pytest
from typer.testing import CliRunner

from qbraid_cli.admin.app import admin_app
from qbraid_cli.admin.headers import DEFAULT_HEADER, VALID_EXTS, HeaderType, get_formatted_header

runner = CliRunner()


def _get_test_file_path(test_type: str, ext=".py") -> str:
    return os.path.join(os.path.dirname(__file__), f"test_{test_type}{ext}")


def _get_test_file(test_type: str, ext: str = ".py") -> str:
    # construct the file name
    file_path = _get_test_file_path(test_type, ext)

    comment_marker = "#" if ext == ".py" else "//"
    updated_header = DEFAULT_HEADER.replace("#", comment_marker)

    if test_type == "no_header":
        with open(file_path, "w") as f:
            f.write("print('hello world')")
    elif test_type == "correct_header":
        with open(file_path, "w") as f:
            f.write(updated_header + "\n\n" + "print('hello world')")
    elif test_type == "old_header":
        with open(file_path, "w") as f:
            f.write(f"{comment_marker} This is an old header\n\n" + "print('hello world')")
    elif test_type == "last_year":
        with open(file_path, "w") as f:
            prev_year_header = f"""{comment_marker} Copyright (c) {str(datetime.datetime.now().year - 1)}, qBraid Development Team
{comment_marker} All rights reserved."""
            f.write(prev_year_header + "\n\n" + "print('hello world')" + "\n")
    else:
        raise ValueError(f"Invalid test type: {test_type}")

    return file_path


def remove_test_file(test_type: str, ext: str = ".py") -> None:
    """Remove the test file."""
    file_path = _get_test_file_path(test_type, ext)
    os.remove(file_path)


def strip_ansi_codes(text):
    """Remove ANSI escape codes from text."""
    ansi_escape = re.compile(r"\x1B[@-_][0-?]*[ -/]*[@-~]")
    return ansi_escape.sub("", text)


def verify_test_result(result, expected_exit_code: int, expected_output: str):
    """Verify the test result."""
    assert expected_output in strip_ansi_codes(result.stdout)
    assert result.exit_code == expected_exit_code


@pytest.mark.parametrize("ext", VALID_EXTS)
def test_header_fix_for_file_with_correct_header(ext):
    """Test that the header fix function does not change the file with the correct header."""
    file_path = _get_test_file("correct_header", ext)
    original_content = open(file_path, "r").read()

    result = runner.invoke(admin_app, [file_path, "--fix"])

    verify_test_result(result, 0, "1 file left unchanged")

    # assert that the file has not been changed
    with open(file_path, "r") as f:
        passed = f.read() == original_content

    remove_test_file("correct_header", ext)

    assert passed


@pytest.mark.parametrize("ext", VALID_EXTS)
def test_header_fix_for_file_with_no_header(ext):
    """Test that the header fix function adds the new header to a file with no header."""
    file_path = _get_test_file("no_header", ext)

    result = runner.invoke(admin_app, [file_path, "--fix"])

    try:
        verify_test_result(result, 0, "1 file fixed")

        comment_marker = "#" if ext == ".py" else "//"

        # assert that the file has the new header
        with open(file_path, "r") as f:
            assert (
                f.read()
                == DEFAULT_HEADER.replace("#", comment_marker)
                + "\n"
                + "print('hello world')"
                + "\n"
            )
    finally:
        remove_test_file("no_header", ext)


@pytest.mark.parametrize("ext", VALID_EXTS)
def test_header_update_for_file_with_old_header(ext):
    """Test that the header fix function updates the header in a file with an old header."""
    file_path = _get_test_file("old_header", ext)

    result = runner.invoke(admin_app, [file_path, "--fix", "-t", "gpl", "-p", "test_project"])

    try:
        verify_test_result(result, 0, "1 file fixed")

        comment_marker = "#" if ext == ".py" else "//"

        # assert that the file has the new header
        with open(file_path, "r") as f:
            assert (
                f.read()
                == get_formatted_header(HeaderType.gpl, "test_project").replace("#", comment_marker)
                + "\n"
                + "print('hello world')"
                + "\n"
            )
    finally:
        remove_test_file("old_header", ext)


def test_current_year_header_for_new_file():
    """Test that the header fix function adds the new header with the current year to a file with no header."""
    file_path = _get_test_file("no_header")

    result = runner.invoke(admin_app, [file_path, "--fix"])

    try:
        verify_test_result(result, 0, "1 file fixed")

        # assert that the file has the new header with the current year
        with open(file_path, "r") as f:
            assert str(datetime.datetime.now().year) in f.read()

    finally:
        remove_test_file("no_header")


def test_no_header_update_for_file_with_last_year_header():
    """Test that the header fix function does not update the header in a file with the last year header."""
    file_path = _get_test_file("last_year")
    original_content = open(file_path, "r").read()

    result = runner.invoke(admin_app, [file_path, "--fix"])

    try:
        verify_test_result(result, 0, "1 file left unchanged")

        # assert that the file has not been changed
        with open(file_path, "r") as f:
            assert f.read() == original_content

    finally:
        remove_test_file("last_year")


def test_files_in_directory():
    """Test that all files in a directory are fixed."""
    test_files = ["no_header", "correct_header", "old_header"]
    _ = [_get_test_file(test_file) for test_file in test_files]

    result = runner.invoke(admin_app, [os.path.dirname(__file__), "--fix"])

    try:
        verify_test_result(result, 0, "2 files fixed")
    finally:
        for test_file in test_files:
            remove_test_file(test_file)


def test_invalid_path():
    """Test that the header fix function returns an error for an invalid path."""
    file_path = "invalid_path"

    result = runner.invoke(admin_app, [file_path, "--fix"])

    verify_test_result(result, 2, f"Path '{file_path}' does not exist")


def test_invalid_header_types():
    """Test that the header fix function returns an error for invalid header types."""
    file_path = _get_test_file("no_header")

    result = runner.invoke(admin_app, [file_path, "--fix", "-t", "invalid_header"])
    try:
        verify_test_result(result, 2, "Invalid value for '--type' / '-t'")
    finally:
        remove_test_file("no_header")


def test_correct_identification_of_bad_headers():
    """Test that the header fix function correctly identifies files with bad headers."""
    file_path = _get_test_file("old_header")

    result = runner.invoke(admin_app, [file_path])

    try:
        verify_test_result(result, 1, "would fix")
    finally:
        remove_test_file("old_header")


def test_non_supported_extensions_are_untouched():
    """Test that the header fix function does not change non-supported files."""
    non_python_file_path = os.path.join(os.path.dirname(__file__), "unsupported_file.txt")

    with open(non_python_file_path, "w") as f:
        f.write("test")

    result = runner.invoke(admin_app, [non_python_file_path, "--fix"])

    try:
        verify_test_result(result, 0, f"No {VALID_EXTS} files present. Nothing to do")
    finally:
        os.remove(non_python_file_path)
