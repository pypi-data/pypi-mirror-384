# Copyright (c) 2024, qBraid Development Team
# All rights reserved.

"""
Unit tests for the default_action function in the configure app.

"""

import configparser
from unittest.mock import patch

import pytest

from qbraid_cli.configure.actions import default_action


@pytest.mark.parametrize(
    "org_model_enabled,side_effect,expected_call_count",
    [
        (False, ["https://new.example.com", "api-key-123"], 2),
        (True, ["https://api.qbraid.com", "api-key-456", "qbraid-org", "default-workspace"], 4),
    ],
)
def test_default_action(org_model_enabled, side_effect, expected_call_count):
    """Test default_action method with mocked dependencies."""
    # Store original value of QBRAID_ORG_MODEL_ENABLED
    import qbraid_cli.configure.actions as actions_module

    original_org_model_enabled = actions_module.QBRAID_ORG_MODEL_ENABLED

    try:
        # Set the org model enabled flag for this test
        actions_module.QBRAID_ORG_MODEL_ENABLED = org_model_enabled

        with (
            patch("qbraid_cli.configure.actions.load_config") as mock_load_config,
            patch("qbraid_cli.configure.actions.prompt_for_config") as mock_prompt,
            patch("qbraid_cli.configure.actions.handle_filesystem_operation") as mock_handle_fs,
            patch("qbraid_cli.configure.actions.Console") as mock_console,
        ):
            # Setup mock returns
            config = configparser.ConfigParser()
            config.add_section("default")
            mock_load_config.return_value = config
            mock_prompt.side_effect = side_effect
            mock_console_instance = mock_console.return_value

            # Call the function to test
            default_action()

            # Verify prompt_for_config was called the expected number of times
            assert mock_prompt.call_count == expected_call_count
            mock_load_config.assert_called_once()
            mock_handle_fs.assert_called_once()
            mock_console_instance.print.assert_called_once_with(
                "\n[bold green]Configuration updated successfully."
            )

    finally:
        # Restore original value
        actions_module.QBRAID_ORG_MODEL_ENABLED = original_org_model_enabled
