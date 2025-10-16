# Copyright (c) 2024, qBraid Development Team
# All rights reserved.

"""
Unit tests for the `qbraid_cli.jobs.validation.handle_jobs_state` function.

"""

from unittest.mock import MagicMock, patch

import pytest
import typer

from qbraid_cli.jobs.validation import handle_jobs_state


def test_handle_jobs_state_not_installed():
    """Test handle_jobs_state when the library is not installed."""
    with patch(
        "qbraid_cli.jobs.validation.run_progress_get_state",
        return_value=("/usr/local/bin/python", {"braket": (False, False)}),
    ):
        action_callback = MagicMock()

        with pytest.raises(typer.Exit):
            assert "Error" in handle_jobs_state("braket", "enable", action_callback).output


@patch("rich.console.Console.print")
def test_handle_jobs_state_already_correct_state(mock_console_print):
    """Test handle_jobs_state when the library is already in the correct state."""

    with patch(
        "qbraid_cli.jobs.validation.run_progress_get_state",
        return_value=("/usr/local/bin/python", {"braket": (True, True)}),
    ):
        action_callback = MagicMock()

        with pytest.raises(typer.Exit):
            handle_jobs_state("braket", "enable", action_callback)

        # Verify console.print is called with the expected messages
        assert mock_console_print.call_count == 1
        action_callback.assert_not_called()


def test_handle_jobs_state_action_needed():
    """Test handle_jobs_state when the library is not in the correct state."""
    with patch(
        "qbraid_cli.jobs.validation.run_progress_get_state",
        return_value=("/usr/local/bin/python", {"braket": (True, False)}),
    ):
        action_callback = MagicMock()

        with patch("rich.console.Console.print") as mock_console_print:
            handle_jobs_state("braket", "enable", action_callback)

        action_callback.assert_called_once()
        # Assuming console.print is not called in this scenario; adjust as needed
        mock_console_print.assert_not_called()
