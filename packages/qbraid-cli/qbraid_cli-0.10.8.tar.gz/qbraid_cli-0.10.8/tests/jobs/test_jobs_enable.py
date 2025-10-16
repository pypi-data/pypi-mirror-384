# Copyright (c) 2024, qBraid Development Team
# All rights reserved.

"""
Unit tests for the `jobs_enable` command in the `qbraid_cli.jobs.app` module.

"""

import importlib
from unittest.mock import patch

import pytest
import typer
from qbraid_core.services.quantum.proxy import SUPPORTED_QJOB_LIBS

from qbraid_cli.jobs.app import jobs_enable

qjobs_libs = list(SUPPORTED_QJOB_LIBS.keys())


@pytest.mark.parametrize("library", qjobs_libs)
def test_library_validation(library):
    """Test library validation function during the jobs enable command."""
    with (
        patch(f"qbraid_cli.jobs.toggle_{library}.enable_{library}") as mock_enable_library,
        patch("qbraid_cli.jobs.validation.validate_library") as mock_validate_library,
    ):
        # Assume `validate_library` callback returns True for simplicity
        mock_enable_library.return_value = None
        mock_validate_library.return_value = True
        with pytest.raises(typer.Exit):
            jobs_enable(library=library)
            mock_validate_library.assert_called_once_with(library)


@pytest.mark.parametrize("library", qjobs_libs)
def test_enable_action_for_supported_library(library):
    """Test the enable action for supported libraries."""
    if importlib.util.find_spec(library) is None:
        with pytest.raises(typer.Exit):
            jobs_enable(library=library)
    else:
        with patch(f"qbraid_cli.jobs.toggle_{library}.enable_{library}") as mock_enable_library:
            with pytest.raises(typer.Exit):
                jobs_enable(library=library)
                mock_enable_library.assert_called_once()


def test_raise_error_for_unsupported_library():
    """Test that an error is raised for an unsupported library during the jobs enable command."""
    with pytest.raises(typer.Exit):
        jobs_enable(library="unsupported_library")


@pytest.mark.parametrize("library", qjobs_libs)
def test_handle_jobs_state_integration(library):
    """Test the handle_jobs_state function during the jobs enable command."""
    with (
        patch("typer.confirm") as mock_confirm,
        patch(f"qbraid_cli.jobs.toggle_{library}.enable_{library}") as mock_enable_library,
        patch("qbraid_cli.jobs.validation.handle_jobs_state") as mock_handle_jobs_state,
    ):
        mock_confirm.return_value = True
        mock_enable_library.return_value = None
        with pytest.raises(typer.Exit):
            jobs_enable(library=library)
            mock_handle_jobs_state.assert_called_once_with(
                library, "enable", any_callable=True
            )  # Use `any_callable=True` or similar approach to signify any function is passed
