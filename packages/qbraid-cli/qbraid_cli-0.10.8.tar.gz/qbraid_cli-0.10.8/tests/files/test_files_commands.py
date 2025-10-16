# Copyright (c) 2024, qBraid Development Team
# All rights reserved.

# pylint: disable=redefined-outer-name

"""
Unit tests for the `qbraid_cli.files.app` module.

"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from typer.testing import CliRunner

from qbraid_cli.files.app import files_app, is_file_less_than_10mb


@pytest.fixture
def runner():
    """Fixture for invoking CLI commands."""
    return CliRunner()


def test_files_upload(runner, tmp_path):
    """Test the `files upload` command."""
    test_file = tmp_path / "test_file.txt"
    test_file.write_text("Test content")

    with patch("qbraid_core.services.storage.FileStorageClient") as mock_client:
        mock_client.return_value.upload_file.return_value = {
            "namespace": "user",
            "objectPath": "test_file.txt",
        }

        result = runner.invoke(files_app, ["upload", str(test_file)])

    assert result.exit_code == 0
    assert "File uploaded successfully!" in result.stdout
    assert "Namespace: 'user'" in result.stdout
    assert "Object path: 'test_file.txt'" in result.stdout


def test_files_upload_with_options(runner, tmp_path):
    """Test the `files upload` command with options."""
    test_file = tmp_path / "test_file.txt"
    test_file.write_text("Test content")

    with patch("qbraid_core.services.storage.FileStorageClient") as mock_client:
        mock_client.return_value.upload_file.return_value = {
            "namespace": "custom",
            "objectPath": "folder/test_file.txt",
        }

        result = runner.invoke(
            files_app,
            [
                "upload",
                str(test_file),
                "--namespace",
                "custom",
                "--object-path",
                "folder/test_file.txt",
                "--overwrite",
            ],
        )

    assert result.exit_code == 0
    assert "File uploaded successfully!" in result.stdout
    assert "Namespace: 'custom'" in result.stdout
    assert "Object path: 'folder/test_file.txt'" in result.stdout


def test_files_download(runner, tmp_path):
    """Test the `files download` command."""
    with patch("qbraid_core.services.storage.FileStorageClient") as mock_client:
        mock_client.return_value.download_file.return_value = tmp_path / "downloaded_file.txt"

        result = runner.invoke(files_app, ["download", "test_file.txt"])

    assert result.exit_code == 0
    assert "File downloaded successfully!" in result.stdout
    assert f"Saved to: '{(tmp_path / 'downloaded_file.txt')}'" in result.stdout.replace("\n", "")


def test_files_download_with_options(runner, tmp_path):
    """Test the `files download` command with options."""
    save_path = tmp_path / "custom_folder"
    save_path.mkdir()

    with patch("qbraid_core.services.storage.FileStorageClient") as mock_client:
        mock_client.return_value.download_file.return_value = save_path / "downloaded_file.txt"

        result = runner.invoke(
            files_app,
            [
                "download",
                "folder/test_file.txt",
                "--namespace",
                "custom",
                "--save-path",
                str(save_path),
                "--overwrite",
            ],
        )

    assert result.exit_code == 0
    assert "File downloaded successfully!" in result.stdout
    assert f"Saved to: '{(save_path / 'downloaded_file.txt')}'" in result.stdout.replace("\n", "")


def test_is_file_less_than_10mb_small_file(tmp_path):
    """Test is_file_less_than_10mb with a file smaller than 10MB."""
    test_file = tmp_path / "small_file.txt"
    test_file.write_text("Small file content")  # Creates a small file

    assert is_file_less_than_10mb(test_file) is True


def test_is_file_less_than_10mb_large_file(tmp_path):
    """Test is_file_less_than_10mb with a file larger than 10MB."""
    test_file = tmp_path / "large_file.txt"

    # Mock the file stat to return size > 10MB
    mock_stat = Mock()
    mock_stat.st_size = 11 * 1024 * 1024  # 11MB

    with patch.object(Path, "stat", return_value=mock_stat):
        assert is_file_less_than_10mb(test_file) is False


def test_is_file_less_than_10mb_nonexistent_file(tmp_path):
    """Test is_file_less_than_10mb with a nonexistent file."""
    nonexistent_file = tmp_path / "nonexistent.txt"
    assert is_file_less_than_10mb(nonexistent_file) is False


def test_is_file_less_than_10mb_exactly_10mb(tmp_path):
    """Test is_file_less_than_10mb with a file exactly 10MB."""
    test_file = tmp_path / "exact_10mb.txt"

    # Mock the file stat to return size = 10MB
    mock_stat = Mock()
    mock_stat.st_size = 10 * 1024 * 1024  # 10MB

    with patch.object(Path, "stat", return_value=mock_stat):
        assert is_file_less_than_10mb(test_file) is False
