# Copyright (c) 2024, qBraid Development Team
# All rights reserved.

"""
Module supporting 'qbraid jobs enable/disable braket' and commands.

"""

import logging
import os
import re
import subprocess
from pathlib import Path
from typing import Optional

import requests
import typer

from qbraid_cli.exceptions import QbraidException
from qbraid_cli.handlers import handle_error, handle_filesystem_operation, run_progress_task

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fetch_botocore_version() -> Optional[str]:
    """Fetch the latest version of the botocore package from the qBraid GitHub repository."""
    url = "https://raw.githubusercontent.com/qBraid/botocore/develop/botocore/__init__.py"
    response = requests.get(url, timeout=5)
    if response.status_code == 200:
        content = response.text
        version_match = re.search(r"__version__\s*=\s*['\"]([^'\"]+)['\"]", content)
        if version_match:
            return version_match.group(1)
    return None


def get_package_data(package: str) -> tuple[str, str, str, str]:
    """Retrieve package version and location data.

    Args:
        package (str): The name of the package to retrieve data for.

    Returns:
        tuple[str, str, str, str]: The installed and latest versions of the package, and the
                                   local site-packages path where it is / would be installed.

    Raises:
        QbraidException: If package version or location data cannot be retrieved.

    """
    # pylint: disable=import-outside-toplevel
    from qbraid_core.system.exceptions import QbraidSystemError
    from qbraid_core.system.executables import get_active_python_path
    from qbraid_core.system.packages import get_active_site_packages_path
    from qbraid_core.system.versions import get_latest_package_version, get_local_package_version

    try:
        python_pathlib = get_active_python_path()
        site_packages_path = get_active_site_packages_path(python_path=python_pathlib)
        installed_version = get_local_package_version(package, python_path=python_pathlib)

        latest_version = None
        if package in ["botocore", "boto3"]:
            latest_version = fetch_botocore_version()
        latest_version = latest_version or get_latest_package_version(package)

    except QbraidSystemError as err:
        raise QbraidException("Failed to retrieve required system and/or package metadata") from err

    return installed_version, latest_version, str(site_packages_path), str(python_pathlib)


def confirm_updates(
    mode: str,
    site_packages_path: str,
    installed_version: Optional[str] = None,
    target_version: Optional[str] = None,
) -> None:
    """
    Prompts the user to proceed with enabling or disabling qBraid Quantum Jobs.

    Args:
        mode (str): The mode of operation, either "enable" or "disable".
        site_packages_path (str): The location of the site-packages directory where
                                  target package(s) will be updated.
        installed_version (optional, str): The installed version of the target package.
        target_version (optional, str): The latest version of the target package available on PyPI.

    Raises:
        ValueError: If an invalid mode is provided.
        typer.Exit: If the user declines to proceed with enabling or disabling qBraid Quantum Jobs.

    """
    core_package = "botocore"
    versioned_package = "boto3"
    if mode == "enable":
        provider = "qBraid"
        update_msg = f"update {versioned_package} and install"
    elif mode == "disable":
        provider = "boto"
        update_msg = "re-install"
    else:
        raise ValueError(f"Invalid mode: {mode}. Expected 'enable' or 'disable'.")

    typer.echo(f"==> WARNING: {provider}/{core_package} package required <==")
    if (
        installed_version is not None
        and target_version is not None
        and installed_version != target_version
    ):
        typer.echo(f"==> WARNING: A different version of {versioned_package} is required. <==")
        typer.echo(f"  current version: {installed_version}")
        typer.echo(f"  target version: {target_version}")

    gerund = mode[:-2].capitalize() + "ing"

    typer.echo(
        f"\n{gerund} quantum jobs will automatically {update_msg} {provider}/{core_package}, "
        "which may cause incompatibilities with the amazon-braket-sdk and/or awscli.\n"
    )
    typer.echo("## Package Plan ##")
    if mode == "enable":
        typer.echo(
            f"  {versioned_package} location: {os.path.join(site_packages_path, versioned_package)}"
        )
    typer.echo(f"  {core_package} location: {os.path.join(site_packages_path, core_package)}\n")

    user_confirmation = typer.confirm("Proceed", default=True)
    if not user_confirmation:
        typer.echo("\nqBraidSystemExit: Exiting.")
        raise typer.Exit()


def aws_configure_dummy() -> None:
    """
    Initializes AWS configuration and credentials files with placeholder values.

    """
    from qbraid_core.services.quantum.proxy_braket import aws_configure

    try:
        handle_filesystem_operation(aws_configure, Path.home() / ".aws")
    except QbraidException:
        handle_error(message="Failed to configure qBraid quantum jobs.")


def enable_braket(auto_confirm: bool = False):
    """Enable qBraid quantum jobs for Amazon Braket."""
    installed, target, path, python_exe = run_progress_task(
        get_package_data, "boto3", description="Solving environment..."
    )

    if not auto_confirm:
        confirm_updates("enable", path, installed_version=installed, target_version=target)
    typer.echo("")

    aws_configure_dummy()  # TODO: possibly add another confirmation for writing aws config files

    try:
        subprocess.check_call([python_exe, "-m", "pip", "install", f"boto3=={target}"])
        subprocess.check_call([python_exe, "-m", "pip", "uninstall", "botocore", "-y", "--quiet"])
        subprocess.check_call(
            [python_exe, "-m", "pip", "install", "git+https://github.com/qBraid/botocore.git"]
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        handle_error(message="Failed to enable qBraid quantum jobs.")

    typer.secho("\nSuccessfully enabled qBraid quantum jobs.", fg=typer.colors.GREEN, bold=True)
    typer.secho("\nTo disable, run: \n\n\t$ qbraid jobs disable braket\n")


def disable_braket(auto_confirm: bool = False):
    """Disable qBraid quantum jobs for Amazon Braket."""
    package = "botocore"
    installed, latest, path, python_exe = run_progress_task(
        get_package_data, package, description="Solving environment..."
    )
    package = f"{package}~={installed}" if installed < latest else package

    if not auto_confirm:
        confirm_updates("disable", path)
    typer.echo("")

    try:
        subprocess.check_call(
            [
                python_exe,
                "-m",
                "pip",
                "install",
                package,
                "--force-reinstall",
            ],
            stderr=subprocess.DEVNULL,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        handle_error(message="Failed to disable qBraid quantum jobs.")

    typer.secho("\nSuccessfully disabled qBraid quantum jobs.", fg=typer.colors.GREEN, bold=True)
    typer.secho("\nTo enable, run: \n\n\t$ qbraid jobs enable braket\n")
