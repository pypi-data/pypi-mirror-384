# Copyright (c) 2024, qBraid Development Team
# All rights reserved.

"""
Unit tests for the `jobs_get` function in the `qbraid_cli.jobs.app` module.

"""

from unittest.mock import patch

import pytest
import typer
from qbraid_core.services.quantum.exceptions import QuantumServiceRequestError
from typer.testing import CliRunner

from qbraid_cli.jobs.app import jobs_get

runner = CliRunner()


@pytest.mark.remote
def test_jobs_get_formatted_output():
    """Test the `jobs_get` function with formatted output (default behavior)."""
    mock_job_data = {
        "id": "test-job-123",
        "status": "COMPLETED",
        "created_at": "2023-03-19T12:00:00Z",
        "result": {"data": "test_result"},
    }
    job_id = "test-job-123"

    with (
        patch("qbraid_core.services.quantum.QuantumClient.get_job", return_value=mock_job_data),
        patch("rich.console.Console.print") as mock_console_print,
    ):
        jobs_get(job_id=job_id, fmt=True)

        # Verify the console was called to print the formatted data (last call should be our data)
        calls = mock_console_print.call_args_list
        assert len(calls) >= 1
        # The last call should be our job data
        assert calls[-1][0][0] == mock_job_data


@pytest.mark.remote
def test_jobs_get_raw_output():
    """Test the `jobs_get` function with raw output (fmt=False)."""
    mock_job_data = {
        "id": "test-job-456",
        "status": "RUNNING",
        "created_at": "2023-03-19T13:00:00Z",
    }
    job_id = "test-job-456"

    with (
        patch("qbraid_core.services.quantum.QuantumClient.get_job", return_value=mock_job_data),
        patch("builtins.print") as mock_print,
    ):
        jobs_get(job_id=job_id, fmt=False)

        # Verify print was called with the raw data
        mock_print.assert_called_once_with(mock_job_data)


@pytest.mark.remote
def test_jobs_get_default_fmt_behavior():
    """Test that `jobs_get` defaults to formatted output when fmt is not specified."""
    mock_job_data = {"id": "test-job-789", "status": "FAILED", "error": "Test error message"}
    job_id = "test-job-789"

    with (
        patch("qbraid_core.services.quantum.QuantumClient.get_job", return_value=mock_job_data),
        patch("rich.console.Console.print") as mock_console_print,
    ):
        jobs_get(job_id=job_id)  # fmt defaults to True

        # Verify the console was called to print the formatted data (last call should be our data)
        calls = mock_console_print.call_args_list
        assert len(calls) >= 1
        # The last call should be our job data
        assert calls[-1][0][0] == mock_job_data


@pytest.mark.remote
def test_jobs_get_quantum_client_error():
    """Test error handling when QuantumClient.get_job raises an exception."""
    job_id = "invalid-job-id"

    with patch(
        "qbraid_core.services.quantum.QuantumClient.get_job",
        side_effect=QuantumServiceRequestError("Job not found"),
    ):
        with pytest.raises(typer.Exit) as exc_info:
            jobs_get(job_id=job_id)

        assert exc_info.value.exit_code == 1


@pytest.mark.remote
def test_jobs_get_empty_job_data():
    """Test handling of empty job data."""
    mock_job_data = {}
    job_id = "empty-job-id"

    with (
        patch("qbraid_core.services.quantum.QuantumClient.get_job", return_value=mock_job_data),
        patch("rich.console.Console.print") as mock_console_print,
    ):
        jobs_get(job_id=job_id, fmt=True)

        # Verify the console was called with empty data (last call should be our data)
        calls = mock_console_print.call_args_list
        assert len(calls) >= 1
        # The last call should be our job data
        assert calls[-1][0][0] == mock_job_data


@pytest.mark.remote
def test_jobs_get_complex_job_data():
    """Test handling of complex job data with nested structures."""
    mock_job_data = {
        "id": "complex-job-123",
        "status": "COMPLETED",
        "metadata": {
            "circuit": {"gates": ["H", "CNOT", "H"]},
            "parameters": {"shots": 1000, "backend": "ibmq_qasm_simulator"},
        },
        "results": {"counts": {"00": 500, "11": 500}, "memory": ["00", "11", "00", "11"]},
    }
    job_id = "complex-job-123"

    with (
        patch("qbraid_core.services.quantum.QuantumClient.get_job", return_value=mock_job_data),
        patch("rich.console.Console.print") as mock_console_print,
    ):
        jobs_get(job_id=job_id, fmt=True)

        # Verify the console was called with complex data (last call should be our data)
        calls = mock_console_print.call_args_list
        assert len(calls) >= 1
        # The last call should be our job data
        assert calls[-1][0][0] == mock_job_data


@pytest.mark.remote
def test_jobs_get_cli_integration_formatted():
    """Test the jobs get command via CLI with formatted output."""
    from qbraid_cli.jobs.app import jobs_app

    mock_job_data = {"id": "cli-test-job", "status": "COMPLETED"}

    with (
        patch("qbraid_core.services.quantum.QuantumClient.get_job", return_value=mock_job_data),
        patch("rich.console.Console.print") as mock_console_print,
    ):
        result = runner.invoke(jobs_app, ["get", "cli-test-job"])

        assert result.exit_code == 0
        calls = mock_console_print.call_args_list
        assert len(calls) >= 1
        # The last call should be our job data
        assert calls[-1][0][0] == mock_job_data


@pytest.mark.remote
def test_jobs_get_cli_integration_raw():
    """Test the jobs get command via CLI with raw output."""
    from qbraid_cli.jobs.app import jobs_app

    mock_job_data = {"id": "cli-raw-job", "status": "RUNNING"}

    with (
        patch("qbraid_core.services.quantum.QuantumClient.get_job", return_value=mock_job_data),
        patch("builtins.print") as mock_print,
    ):
        result = runner.invoke(jobs_app, ["get", "cli-raw-job", "--no-fmt"])

        assert result.exit_code == 0
        mock_print.assert_called_once_with(mock_job_data)
