# Copyright (c) 2024, qBraid Development Team
# All rights reserved.

"""
Unit tests for the devices_list function in the devices app.

"""

from unittest.mock import MagicMock, patch

import pytest
from qbraid_core.services.quantum.exceptions import QuantumServiceRequestError
from typer.testing import CliRunner

from qbraid_cli.devices.app import devices_list

runner = CliRunner()


@pytest.mark.remote
def test_devices_list_no_results():
    """Test when no results are returned from the API."""
    with (
        patch("qbraid_core.services.quantum.process_job_data", return_value=([], 0)),
        patch("rich.console.Console.print") as mock_console_print,
    ):
        devices_list()
        assert "No results matching given criteria" in str(mock_console_print.call_args)


@pytest.mark.remote
def test_quantum_client_search_devices_failure():
    """Test that QuantumClient.search_devices correctly raises an exception."""
    with patch(
        "qbraid_core.services.quantum.QuantumClient.search_devices",
        side_effect=QuantumServiceRequestError("Failed to fetch device data"),
    ):
        with pytest.raises(QuantumServiceRequestError) as exc_info:
            devices_list()

        assert str(exc_info.value) == "Failed to fetch device data"


@pytest.mark.remote
def test_devices_list_error_handling():
    """Test error handling when an error occurs during device data retrieval."""
    with (
        patch("qbraid_cli.handlers.run_progress_task", return_value=(MagicMock(), MagicMock())),
        patch(
            "qbraid_core.services.quantum.QuantumClient.search_devices",
            side_effect=QuantumServiceRequestError("Failed to fetch device data."),
        ),
    ):
        with pytest.raises(QuantumServiceRequestError) as exc_info:
            devices_list()

        assert str(exc_info.value) == "Failed to fetch device data."


@pytest.mark.remote
def test_output_formatting_console():
    """Test the output formatting in the console."""
    mock_device_data = [("AWS", "Quantum Computer", "dev_123", "ONLINE")]

    with (
        patch(
            "qbraid_core.services.quantum.process_job_data",
            return_value=(mock_device_data, MagicMock()),
        ),
        patch("rich.console.Console.print") as mock_console_print,
    ):
        devices_list()

        mock_console_print.assert_called()
