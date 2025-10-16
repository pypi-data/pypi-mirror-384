# Copyright (c) 2024, qBraid Development Team
# All rights reserved.

"""
Unit tests for the get_package_data function in the toggle_braket module.

"""

from unittest.mock import patch

import pytest
from qbraid_core.system.exceptions import QbraidSystemError

from qbraid_cli.jobs.toggle_braket import QbraidException, get_package_data


def test_successful_data_retrieval():
    """
    Verify that the function returns the correct tuple of installed version,
    latest version, and site-packages path for a known package.
    """
    package_name = "example_package"
    expected_installed_version = "1.0.0"
    expected_latest_version = "1.0.1"
    expected_site_packages_path = "/usr/local/lib/python3.9/site-packages"
    expected_python_exe = "/usr/local/bin/python"

    with (
        patch(
            "qbraid_core.system.versions.get_local_package_version",
            return_value=expected_installed_version,
        ),
        patch(
            "qbraid_core.system.versions.get_latest_package_version",
            return_value=expected_latest_version,
        ),
        patch(
            "qbraid_core.system.packages.get_active_site_packages_path",
            return_value=expected_site_packages_path,
        ),
        patch(
            "qbraid_core.system.executables.get_active_python_path",
            return_value=expected_python_exe,
        ),
    ):
        installed_version, latest_version, site_packages_path, python_exe = get_package_data(
            package_name
        )

        assert installed_version == expected_installed_version
        assert latest_version == expected_latest_version
        assert site_packages_path == expected_site_packages_path
        assert python_exe == expected_python_exe


def test_error_during_local_version_retrieval():
    """
    Ensure the function raises a QbraidException when either get_local_package_version or
    get_latest_package_version fails.
    """
    package_name = "faulty_package"
    with (
        patch(
            "qbraid_core.system.versions.get_local_package_version",
            side_effect=QbraidSystemError("Error"),
        ),
        patch("qbraid_core.system.versions.get_latest_package_version") as mock_latest_version,
    ):
        mock_latest_version.return_value = (
            "1.0.1"  # This won't be reached but is set for completeness
        )
        with pytest.raises(QbraidException) as exc_info:
            get_package_data(package_name)
        assert "Failed to retrieve required system and/or package metadata" in str(exc_info.value)


def test_error_during_latest_version_retrieval():
    """
    Check if the function correctly raises a QbraidException
    when get_active_site_packages_path fails.
    """
    package_name = "faulty_package"
    with (
        patch("qbraid_core.system.versions.get_local_package_version") as mock_local_version,
        patch(
            "qbraid_core.system.versions.get_latest_package_version",
            side_effect=QbraidSystemError("Error"),
        ),
    ):
        mock_local_version.return_value = "1.0.0"  # This is expected to be successful
        with pytest.raises(QbraidException) as exc_info:
            get_package_data(package_name)
        assert "Failed to retrieve required system and/or package metadata" in str(exc_info.value)


def test_non_existent_package():
    """
    Confirm that the function behaves as expected
    (either by returning versions as None or raising an exception),
    when a non-existent package is queried.
    """
    package_name = "imaginary_package"
    expected_installed_version = None
    expected_latest_version = None
    expected_site_packages_path = "/usr/local/lib/python3.10/site-packages"
    expected_python_exe = "/usr/local/bin/python"

    with (
        patch(
            "qbraid_core.system.versions.get_local_package_version",
            return_value=expected_installed_version,
        ),
        patch(
            "qbraid_core.system.versions.get_latest_package_version",
            return_value=expected_latest_version,
        ),
        patch(
            "qbraid_core.system.packages.get_active_site_packages_path",
            return_value=expected_site_packages_path,
        ),
        patch(
            "qbraid_core.system.executables.get_active_python_path",
            return_value=expected_python_exe,
        ),
    ):
        installed_version, latest_version, site_packages_path, python_exe = get_package_data(
            package_name
        )

        assert (
            installed_version == expected_installed_version
        ), "Installed version should be None for a non-existent package"
        assert (
            latest_version == expected_latest_version
        ), "Latest version should be None for a non-existent package"
        assert (
            site_packages_path == expected_site_packages_path
        ), "The site-packages path should still be retrievable"
        assert (
            python_exe == expected_python_exe
        ), "The python executable should still be retrievable"


def test_package_no_updates_available():
    """Verify the function correctly identifies when the installed version is the latest."""
    package_name = "up_to_date_package"
    expected_installed_version = "1.0.1"
    expected_latest_version = "1.0.1"  # Installed version is the latest
    expected_site_packages_path = "/usr/local/lib/python3.10/site-packages"
    expected_python_exe = "/usr/local/bin/python"

    with (
        patch(
            "qbraid_core.system.versions.get_local_package_version",
            return_value=expected_installed_version,
        ),
        patch(
            "qbraid_core.system.versions.get_latest_package_version",
            return_value=expected_latest_version,
        ),
        patch(
            "qbraid_core.system.packages.get_active_site_packages_path",
            return_value=expected_site_packages_path,
        ),
        patch(
            "qbraid_core.system.executables.get_active_python_path",
            return_value=expected_python_exe,
        ),
    ):
        installed_version, latest_version, site_packages_path, python_exe = get_package_data(
            package_name
        )

        assert (
            installed_version == expected_installed_version
        ), "Installed version should match the expected version"
        assert (
            latest_version == expected_latest_version
        ), "Latest version should match the installed version indicating no updates"
        assert (
            site_packages_path == expected_site_packages_path
        ), "The site-packages path should be correctly retrieved"
        assert (
            python_exe == expected_python_exe
        ), "The python executable should still be retrievable"
