# Copyright (c) 2024, qBraid Development Team
# All rights reserved.

"""
Unit tests for the configure_set function in the configure app.

"""

from unittest.mock import MagicMock, patch

from qbraid_cli.configure.app import configure_set


def test_configure_set(capsys):
    """Test the configure_set function."""
    mock_load_config = MagicMock(return_value={"default": {"existing_config": "existing_value"}})
    mock_save_config = MagicMock()

    with (
        patch("qbraid_core.config.load_config", mock_load_config),
        patch("qbraid_core.config.save_config", mock_save_config),
    ):
        configure_set("test_config", "test_value", "test_profile")

        # Use capsys to capture the output after the function call
        captured = capsys.readouterr()

    # Assertions to check if load_config and save_config were called correctly
    mock_load_config.assert_called_once()
    expected_config = {
        "default": {"existing_config": "existing_value"},
        "test_profile": {"test_config": "test_value"},
    }
    mock_save_config.assert_called_once_with(expected_config)

    # Check the output message
    assert "Configuration updated successfully." in captured.out
