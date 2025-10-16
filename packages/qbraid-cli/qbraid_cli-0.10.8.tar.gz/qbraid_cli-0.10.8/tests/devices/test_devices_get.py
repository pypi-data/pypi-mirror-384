# Copyright (c) 2024, qBraid Development Team
# All rights reserved.

"""
Unit tests for the `devices_get` function in the `qbraid_cli.devices.app` module.

"""

from unittest.mock import MagicMock, patch

import pytest
import typer
from qbraid_core.services.quantum.exceptions import QuantumServiceRequestError
from typer.testing import CliRunner

from qbraid_cli.devices.app import devices_get

runner = CliRunner()


@pytest.mark.remote
def test_devices_get_formatted_output():
    """Test the `devices_get` function with formatted output (default behavior)."""
    mock_device_data = {
        "id": "test-device-123",
        "name": "Test Quantum Computer",
        "provider": "AWS",
        "status": "ONLINE",
        "type": "QPU",
        "properties": {"qubits": 5, "connectivity": "all-to-all"},
    }
    device_id = "test-device-123"

    with (
        patch(
            "qbraid_core.services.quantum.QuantumClient.get_device", return_value=mock_device_data
        ),
        patch("rich.console.Console.print") as mock_console_print,
    ):
        devices_get(device_id=device_id, fmt=True)

        # Verify the console was called to print the formatted data (last call should be our data)
        calls = mock_console_print.call_args_list
        assert len(calls) >= 1
        # The last call should be our device data
        assert calls[-1][0][0] == mock_device_data


@pytest.mark.remote
def test_devices_get_raw_output():
    """Test the `devices_get` function with raw output (fmt=False)."""
    mock_device_data = {
        "id": "test-device-456",
        "name": "Test Simulator",
        "provider": "IBM",
        "status": "OFFLINE",
        "type": "SIMULATOR",
    }
    device_id = "test-device-456"

    with (
        patch(
            "qbraid_core.services.quantum.QuantumClient.get_device", return_value=mock_device_data
        ),
        patch("builtins.print") as mock_print,
    ):
        devices_get(device_id=device_id, fmt=False)

        # Verify print was called with the raw data
        mock_print.assert_called_once_with(mock_device_data)


@pytest.mark.remote
def test_devices_get_default_fmt_behavior():
    """Test that `devices_get` defaults to formatted output when fmt is not specified."""
    mock_device_data = {
        "id": "test-device-789",
        "name": "Default Test Device",
        "provider": "IonQ",
        "status": "RETIRED",
        "type": "QPU",
    }
    device_id = "test-device-789"

    with (
        patch(
            "qbraid_core.services.quantum.QuantumClient.get_device", return_value=mock_device_data
        ),
        patch("rich.console.Console.print") as mock_console_print,
    ):
        devices_get(device_id=device_id)  # fmt defaults to True

        # Verify the console was called to print the formatted data (last call should be our data)
        calls = mock_console_print.call_args_list
        assert len(calls) >= 1
        # The last call should be our device data
        assert calls[-1][0][0] == mock_device_data


@pytest.mark.remote
def test_devices_get_quantum_client_error():
    """Test error handling when QuantumClient.get_device raises an exception."""
    device_id = "invalid-device-id"

    with patch(
        "qbraid_core.services.quantum.QuantumClient.get_device",
        side_effect=QuantumServiceRequestError("Device not found"),
    ):
        with pytest.raises(typer.Exit) as exc_info:
            devices_get(device_id=device_id)

        assert exc_info.value.exit_code == 1


@pytest.mark.remote
def test_devices_get_empty_device_data():
    """Test handling of empty device data."""
    mock_device_data = {}
    device_id = "empty-device-id"

    with (
        patch(
            "qbraid_core.services.quantum.QuantumClient.get_device", return_value=mock_device_data
        ),
        patch("rich.console.Console.print") as mock_console_print,
    ):
        devices_get(device_id=device_id, fmt=True)

        # Verify the console was called with empty data (last call should be our data)
        calls = mock_console_print.call_args_list
        assert len(calls) >= 1
        # The last call should be our device data
        assert calls[-1][0][0] == mock_device_data


@pytest.mark.remote
def test_devices_get_complex_device_data():
    """Test handling of complex device data with nested structures."""
    mock_device_data = {
        "id": "complex-device-123",
        "name": "Advanced Quantum Computer",
        "provider": "Rigetti",
        "status": "ONLINE",
        "type": "QPU",
        "specifications": {
            "qubits": 32,
            "connectivity": "nearest-neighbor",
            "gate_fidelity": 0.99,
            "coherence_time": "100μs",
        },
        "calibration": {
            "last_calibrated": "2023-03-19T12:00:00Z",
            "next_calibration": "2023-03-26T12:00:00Z",
            "calibration_data": {
                "readout_fidelity": 0.95,
                "single_qubit_gate_fidelity": 0.99,
                "two_qubit_gate_fidelity": 0.97,
            },
        },
    }
    device_id = "complex-device-123"

    with (
        patch(
            "qbraid_core.services.quantum.QuantumClient.get_device", return_value=mock_device_data
        ),
        patch("rich.console.Console.print") as mock_console_print,
    ):
        devices_get(device_id=device_id, fmt=True)

        # Verify the console was called with complex data (last call should be our data)
        calls = mock_console_print.call_args_list
        assert len(calls) >= 1
        # The last call should be our device data
        assert calls[-1][0][0] == mock_device_data


@pytest.mark.remote
def test_devices_get_cli_integration_formatted():
    """Test the devices get command via CLI with formatted output."""
    from qbraid_cli.devices.app import devices_app

    mock_device_data = {"id": "cli-test-device", "name": "CLI Test Device", "status": "ONLINE"}

    with (
        patch(
            "qbraid_core.services.quantum.QuantumClient.get_device", return_value=mock_device_data
        ),
        patch("rich.console.Console.print") as mock_console_print,
    ):
        result = runner.invoke(devices_app, ["get", "cli-test-device"])

        assert result.exit_code == 0
        calls = mock_console_print.call_args_list
        assert len(calls) >= 1
        # The last call should be our device data
        assert calls[-1][0][0] == mock_device_data


@pytest.mark.remote
def test_devices_get_cli_integration_raw():
    """Test the devices get command via CLI with raw output."""
    from qbraid_cli.devices.app import devices_app

    mock_device_data = {"id": "cli-raw-device", "name": "CLI Raw Device", "status": "OFFLINE"}

    with (
        patch(
            "qbraid_core.services.quantum.QuantumClient.get_device", return_value=mock_device_data
        ),
        patch("builtins.print") as mock_print,
    ):
        result = runner.invoke(devices_app, ["get", "cli-raw-device", "--no-fmt"])

        assert result.exit_code == 0
        mock_print.assert_called_once_with(mock_device_data)


@pytest.mark.remote
def test_devices_get_different_provider_devices():
    """Test getting devices from different providers."""
    providers = ["AWS", "IBM", "IonQ", "Rigetti", "OQC", "QuEra"]

    for provider in providers:
        mock_device_data = {
            "id": f"{provider.lower()}-device-123",
            "name": f"{provider} Test Device",
            "provider": provider,
            "status": "ONLINE",
            "type": "QPU",
        }
        device_id = f"{provider.lower()}-device-123"

        with (
            patch(
                "qbraid_core.services.quantum.QuantumClient.get_device",
                return_value=mock_device_data,
            ),
            patch("rich.console.Console.print") as mock_console_print,
        ):
            devices_get(device_id=device_id, fmt=True)

            # Verify the console was called with the correct data (last call should be our data)
            calls = mock_console_print.call_args_list
            assert len(calls) >= 1
            # The last call should be our device data
            assert calls[-1][0][0] == mock_device_data


@pytest.mark.remote
def test_devices_get_different_status_devices():
    """Test getting devices with different statuses."""
    statuses = ["ONLINE", "OFFLINE", "RETIRED"]

    for status in statuses:
        mock_device_data = {
            "id": f"status-{status.lower()}-device",
            "name": f"Status {status} Device",
            "provider": "Test Provider",
            "status": status,
            "type": "QPU",
        }
        device_id = f"status-{status.lower()}-device"

        with (
            patch(
                "qbraid_core.services.quantum.QuantumClient.get_device",
                return_value=mock_device_data,
            ),
            patch("rich.console.Console.print") as mock_console_print,
        ):
            devices_get(device_id=device_id, fmt=True)

            # Verify the console was called with the correct data (last call should be our data)
            calls = mock_console_print.call_args_list
            assert len(calls) >= 1
            # The last call should be our device data
            assert calls[-1][0][0] == mock_device_data
