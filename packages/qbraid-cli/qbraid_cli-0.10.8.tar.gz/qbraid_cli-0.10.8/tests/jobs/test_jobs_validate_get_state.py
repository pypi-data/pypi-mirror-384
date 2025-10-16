# Copyright (c) 2024, qBraid Development Team
# All rights reserved.

"""
Unit tests for the get_state function in the validation module.

"""

from unittest.mock import patch

import pytest

from qbraid_cli.jobs.validation import get_state, run_progress_get_state


@patch("qbraid_core.services.quantum.QuantumClient.qbraid_jobs_state")
def test_get_state_specific_library(mock_qbraid_jobs_state):
    """Test the get_state function for a specific library."""
    library = "braket"
    python_exe = "/usr/bin/python"
    supported, enabled = True, False
    mock_qbraid_jobs_state.return_value = {
        "exe": python_exe,
        "libs": {
            library: {
                "supported": supported,
                "enabled": enabled,
            }
        },
    }
    result = get_state(library)
    expected = (python_exe, {library: (supported, enabled)})
    mock_qbraid_jobs_state.assert_called_once_with(device_lib=library)
    assert result == expected, f"Expected state for {library} to be correctly returned"


@pytest.mark.parametrize(
    "library,mock_return,expected",
    [
        (
            "braket",
            {"exe": "/usr/bin/python", "libs": {"braket": {"supported": True, "enabled": False}}},
            (True, False),
        ),
        (
            "test",
            {"exe": "/usr/bin/python", "libs": {"test": {"supported": False, "enabled": False}}},
            (False, False),
        ),
    ],
)
@patch("qbraid_core.services.quantum.QuantumClient.qbraid_jobs_state")
def test_get_state_multiple_libraries(mock_qbraid_jobs_state, library, mock_return, expected):
    """Test the get_state function when there are multiple libraries."""
    mock_qbraid_jobs_state.return_value = mock_return

    result = get_state(library)
    mock_qbraid_jobs_state.assert_called_once_with(device_lib=library)
    assert result == (
        "/usr/bin/python",
        {library: expected},
    ), f"Expected state for {library} to be correctly returned"


@patch("qbraid_cli.jobs.validation.get_state")
@patch("qbraid_cli.jobs.validation.run_progress_task")
def test_run_progress_get_state_with_library(mock_run_progress_task, mock_get_state):
    """Test run_progress_get_state with braket library."""
    library = "braket"
    # Configure the mock for get_state if necessary, e.g., mock_get_state.return_value = {}

    run_progress_get_state(library)

    # Verifying run_progress_task is called correctly
    mock_run_progress_task.assert_called_once()
    _, kwargs = mock_run_progress_task.call_args
    assert kwargs["description"] == "Collecting package metadata..."
    assert kwargs["error_message"] == f"Failed to collect {library} package metadata."
    # Verifying get_state is intended to be
    # called with the correct arguments
    mock_get_state.assert_not_called()


@patch("qbraid_cli.jobs.validation.get_state")
@patch("qbraid_cli.jobs.validation.run_progress_task")
def test_run_progress_get_state_no_library(mock_run_progress_task, mock_get_state):
    """Test run_progress_get_state without a library."""
    run_progress_get_state()

    mock_run_progress_task.assert_called_once()
    _, kwargs = mock_run_progress_task.call_args
    assert kwargs["description"] == "Collecting package metadata..."
    assert kwargs["error_message"] == "Failed to collect None package metadata."
    mock_get_state.assert_not_called()  # As above
