# Copyright (c) 2024, qBraid Development Team
# All rights reserved.

# pylint: disable=unused-argument

"""
Unit tests for commands and helper functions in the 'qbraid envs' namespace.

"""

from unittest.mock import call, patch

from qbraid_cli.kernels.app import kernels_list


def mock_is_exe(path):
    """Mock function checking if given path is a valid executable."""
    return path == "/path/to/bin/python3", "-m", "ipykernel_launcher", "-f", "test"


@patch("qbraid_core.services.environments.kernels.get_all_kernels", return_value={})
@patch("qbraid_cli.kernels.app.Console")
def test_kernels_list_no_active_kernels(mock_console, mock_list_kernels):
    """Test listing kernels when no kernels are active."""

    kernels_list()

    expected_calls = [
        call("No qBraid kernels are active."),
        call("\nUse 'qbraid kernels add' to add a new kernel."),
    ]
    actual_calls = mock_console.return_value.print.call_args_list
    print(actual_calls, "actual_calls")
    assert actual_calls == expected_calls


@patch(
    "qbraid_core.services.environments.kernels.get_all_kernels",
    return_value={"python3": {"resource_dir": "/path/to/python3/kernel"}},
)
@patch("qbraid_cli.kernels.app.Console")
def test_kernels_list_default_python3_kernel_present(mock_console, mock_list_kernels):
    """Test listing kernels when the default python3 kernel is present."""

    kernels_list()

    expected_calls = [
        call("# qbraid kernels:\n#\n\npython3          /path/to/python3/kernel"),
    ]
    actual_calls = mock_console.return_value.print.call_args_list
    assert actual_calls == expected_calls


@patch(
    "qbraid_core.services.environments.kernels.get_all_kernels",
    return_value={
        "python3": {"resource_dir": "/path/to/python3/kernel"},
        "another_kernel": {
            "resource_dir": "/path/to/another/kernel",
            "spec": {
                "display_name": "Another Kernel",
                "argv": ["/path/to/bin/python3", "-m", "ipykernel_launcher", "-f", "test"],
            },
        },
    },
)
@patch("qbraid_cli.kernels.app.Console")
def test_kernels_list_multiple_kernels_available(mock_console, mock_list_kernels):
    """Test listing multiple kernels when multiple kernels are available."""

    with patch("qbraid_core.services.environments.kernels.is_exe", mock_is_exe):
        kernels_list()

    expected_calls = [
        call(
            "# qbraid kernels:\n#\n\npython3                 "
            "/path/to/python3/kernel\nanother_kernel          "
            "/path/to/another/kernel"
        ),
    ]
    actual_calls = mock_console.return_value.print.call_args_list
    assert actual_calls == expected_calls
