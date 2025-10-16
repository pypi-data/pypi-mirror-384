# Copyright (c) 2025, qBraid Development Team
# All rights reserved.

"""
Unit tests for the configure list and get commands.
"""

from unittest.mock import MagicMock, patch

import pytest
import typer

from qbraid_cli.configure.app import configure_get, configure_list


def test_configure_list_empty_profile(capsys):
    """Test configure_list with an empty default profile."""
    mock_load_config = MagicMock(return_value={"default": {}})

    with patch("qbraid_core.config.load_config", mock_load_config):
        configure_list()
        captured = capsys.readouterr()
        assert "No configuration values found in default profile." in captured.out


def test_configure_list_missing_profile(capsys):
    """Test configure_list with a missing default profile."""
    mock_load_config = MagicMock(return_value={})

    with patch("qbraid_core.config.load_config", mock_load_config):
        with pytest.raises(typer.Exit):
            configure_list()
        captured = capsys.readouterr()
        assert "Default profile not found in configuration." in captured.out


def test_configure_list_with_values(capsys):
    """Test configure_list with various configuration values."""
    mock_config = {
        "default": {
            "api-key": "abcdef123456",
            "refresh-token": "xyz987654321",
            "url": "https://example.com",
        }
    }
    mock_load_config = MagicMock(return_value=mock_config)

    with patch("qbraid_core.config.load_config", mock_load_config):
        configure_list()
        captured = capsys.readouterr()

        # Check that sensitive values are masked
        assert "*****456" in captured.out  # last 3 chars of api-key
        assert "*****321" in captured.out  # last 3 chars of refresh-token
        # Check that non-sensitive values are shown in full
        assert "https://example.com" in captured.out


def test_configure_list_with_org_enabled_config(capsys):
    """Test configure_list with organization and workspace when org model is enabled."""
    mock_config = {
        "default": {
            "api-key": "abcdef123456",
            "refresh-token": "xyz987654321",
            "url": "https://example.com",
            "organization": "my-org",
            "workspace": "my-workspace",
        }
    }
    mock_load_config = MagicMock(return_value=mock_config)
    with patch("qbraid_cli.configure.actions.QBRAID_ORG_MODEL_ENABLED", True):
        with patch("qbraid_core.config.load_config", mock_load_config):
            configure_list()
            captured = capsys.readouterr()

            # Check that sensitive values are masked
            assert "*****456" in captured.out  # last 3 chars of api-key
            assert "*****321" in captured.out  # last 3 chars of refresh-token
            # Check that non-sensitive values are shown in full
            assert "https://example.com" in captured.out
            assert "my-org" in captured.out
            assert "my-workspace" in captured.out


def test_configure_get_success(capsys):
    """Test configure_get with an existing configuration value."""
    mock_config = {"default": {"test-key": "test-value"}}
    mock_load_config = MagicMock(return_value=mock_config)

    with patch("qbraid_core.config.load_config", mock_load_config):
        configure_get("test-key", "default")
        captured = capsys.readouterr()
        assert "test-value" in captured.out


def test_configure_get_missing_profile(capsys):
    """Test configure_get with a missing profile."""
    mock_config = {}
    mock_load_config = MagicMock(return_value=mock_config)

    with patch("qbraid_core.config.load_config", mock_load_config):
        with pytest.raises(typer.Exit):
            configure_get("test-key", "missing-profile")
        captured = capsys.readouterr()
        assert "Profile 'missing-profile' not found in configuration." in captured.out


def test_configure_get_missing_key(capsys):
    """Test configure_get with a missing configuration key."""
    mock_config = {"default": {}}
    mock_load_config = MagicMock(return_value=mock_config)

    with patch("qbraid_core.config.load_config", mock_load_config):
        with pytest.raises(typer.Exit):
            configure_get("missing-key", "default")
        captured = capsys.readouterr()
        assert "Configuration 'missing-key' not found in profile 'default'." in captured.out
