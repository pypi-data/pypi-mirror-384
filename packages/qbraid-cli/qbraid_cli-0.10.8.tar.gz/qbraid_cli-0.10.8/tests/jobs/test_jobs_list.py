# Copyright (c) 2024, qBraid Development Team
# All rights reserved.

"""
Unit tests for the `jobs_list` function in the `qbraid_cli.jobs.app` module.

"""

from unittest.mock import patch

import pytest

from qbraid_cli.jobs.app import jobs_list


@pytest.mark.remote
def test_jobs_list_with_limit():
    """Test the `jobs_list` function with a limit parameter."""
    mock_raw_data = [
        ("job_id_1", "2023-03-19 12:00", "COMPLETED"),
        ("job_id_2", "2023-03-18 11:00", "FAILED"),
    ]
    mock_message = f"Displaying {len(mock_raw_data)} most recent jobs"
    mock_job_data = (mock_raw_data, mock_message)
    limit = 5

    with (
        patch("qbraid_core.services.quantum.process_job_data", return_value=mock_job_data),
        patch("rich.console.Console.print") as mock_console_print,
    ):
        jobs_list(limit=limit)

        assert mock_console_print.call_count >= len(
            mock_job_data
        ), "Console should print each job and possibly more for headers/executable."


@pytest.mark.remote
def test_jobs_list_output_formatting_console():
    """Test the jobs list output formatting in the console."""
    mock_raw_data = [("job_id_1", "2023-03-19 12:00", "COMPLETED")]
    mock_message = f"Displaying {len(mock_raw_data)} most recent jobs"
    mock_job_data = (mock_raw_data, mock_message)

    with (
        patch("qbraid_core.services.quantum.process_job_data", return_value=mock_job_data),
        patch("rich.console.Console.print") as mock_console_print,
    ):
        jobs_list(limit=1)
        mock_console_print.assert_called()
