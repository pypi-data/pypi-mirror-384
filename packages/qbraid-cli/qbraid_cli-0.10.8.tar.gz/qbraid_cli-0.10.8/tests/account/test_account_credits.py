# Copyright (c) 2024, qBraid Development Team
# All rights reserved.

"""
Unit tests for the 'qbraid account credits' command.

"""

from unittest.mock import patch

from typer.testing import CliRunner

from qbraid_cli.account import account_app

runner = CliRunner()


def test_account_credits_success():
    """Test the 'qbraid account credts' command with a successful response."""
    credits_value = 100.4573

    class MockQbraidClient:  # pylint: disable=too-few-public-methods
        """Mock class for the QbraidClient."""

        def user_credits_value(self):
            """ "Mock user_credits_value method."""
            return credits_value

    with (
        patch("qbraid_cli.handlers.run_progress_task") as mock_run_progress_task,
        patch("qbraid_core.QbraidClient") as mock_qbraid_client,
    ):
        mock_response = credits_value
        mock_qbraid_client.return_value = MockQbraidClient()

        # Setup mock for run_progress_task to return the credits directly
        mock_run_progress_task.return_value = mock_response

        result = runner.invoke(account_app, ["credits"])

        assert result.exit_code == 0
        assert "qBraid credits remaining:" in result.output
        assert str(credits_value) in result.output


def test_account_info_success():
    """Test the 'qbraid account info' command with a successful response."""
    mock_info = {
        "_id": "123456789",
        "userName": "mockUser",
        "email": "mock@example.com",
        "joinedDate": "2022-03-10T03:52:08.743Z",
        "activePlan": "Free",
        "role": "guest",
    }

    class MockQbraidSession:  # pylint: disable=too-few-public-methods
        """Mock class for the QbraidSession."""

        def get_user(self):
            """ "Mock get_user method."""
            return {
                "_id": "123456789",
                "userName": "mockUser",
                "email": "mock@example.com",
                "createdAt": "2022-03-10T03:52:08.743Z",
                "activePlan": "Free",
                "role": "guest",
            }

    with (
        patch("qbraid_cli.handlers.run_progress_task") as mock_run_progress_task,
        patch("qbraid_core.QbraidSession") as mock_qbraid_session,
    ):
        mock_response = mock_info
        mock_qbraid_session.return_value = MockQbraidSession()

        # Setup mock for run_progress_task to return the user info directly
        mock_run_progress_task.return_value = mock_response

        result = runner.invoke(account_app, ["info"])

        assert result.exit_code == 0
        for key, value in mock_info.items():
            assert key in result.output
            assert str(value) in result.output
