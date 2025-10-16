# Copyright (c) 2024, qBraid Development Team
# All rights reserved.

"""
Unit tests for the `qbraid_cli.jobs.app.jobs_state` function.

"""

from io import StringIO
from unittest.mock import patch

import pytest
import typer

from qbraid_cli.jobs.app import jobs_state


@patch("sys.stdout", new_callable=StringIO)
def test_output_formatting_and_display(mock_stdout):
    """Test the output formatting and display of the jobs_state function."""
    # Assuming a utility or mock setup that captures console output
    with pytest.raises(typer.Exit):
        with patch(
            "qbraid_cli.jobs.validation.run_progress_get_state",
            return_value={"braket": (True, True)},
        ):
            jobs_state()

            output = mock_stdout.getvalue()
            print(output)
            assert "Library" in output
            assert "State" in output
