# Copyright (c) 2024, qBraid Development Team
# All rights reserved.

"""
Unit tests for the `jobs_disable` command in the `qbraid_cli.jobs.app` module.

"""

from unittest.mock import patch

import pytest
import typer
from qbraid_core.services.quantum.proxy import SUPPORTED_QJOB_LIBS

from qbraid_cli.jobs.app import jobs_disable

qjob_libs = list(SUPPORTED_QJOB_LIBS.keys())


@pytest.mark.parametrize("library", qjob_libs)
def test_library_validation_on_disable(library):
    """Test library validation function during the jobs disable command."""
    with (
        patch(
            "qbraid_cli.jobs.validation.validate_library", return_value=library
        ) as mock_validate_library,
        patch("typer.confirm", return_value=True),
    ):  # Mocking typer.confirm to simulate user confirmation
        with pytest.raises(typer.Exit):
            jobs_disable(library=library)
            mock_validate_library.assert_called_once_with(library)


def test_error_for_unsupported_library_on_disable():
    """Test that an error is raised for an unsupported library during the jobs disable command."""
    with pytest.raises(typer.Exit):
        jobs_disable(library="unsupported_library")


@pytest.mark.parametrize("library", qjob_libs)
def test_handle_jobs_state_integration_on_disable(library):
    """Test the handle_jobs_state function during the jobs disable command."""
    with (
        patch(f"qbraid_cli.jobs.toggle_{library}.disable_{library}"),
        patch("qbraid_cli.jobs.validation.handle_jobs_state") as mock_handle_jobs_state,
    ):
        with pytest.raises(typer.Exit):
            jobs_disable(library=library)
            mock_handle_jobs_state.assert_called_once_with(
                library, "disable", any_callable=True
            )  # Use `any_callable=True` or a similar approach
