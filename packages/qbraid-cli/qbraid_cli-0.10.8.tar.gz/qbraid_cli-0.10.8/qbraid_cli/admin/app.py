# Copyright (c) 2024, qBraid Development Team
# All rights reserved.

"""
Module defining commands in the 'qbraid admin' namespace.

"""

from typing import Optional

import typer

from qbraid_cli.admin.headers import HeaderType, check_and_fix_headers
from qbraid_cli.admin.validation import validate_paths_exist

admin_app = typer.Typer(
    help="CI/CD commands for qBraid maintainers.",
    pretty_exceptions_show_locals=False,
    no_args_is_help=True,
)


@admin_app.command(name="headers")
def admin_headers(
    src_paths: list[str] = typer.Argument(
        ..., help="Source file or directory paths to verify.", callback=validate_paths_exist
    ),
    header_type: HeaderType = typer.Option(
        "default", "--type", "-t", help="Type of header to use."
    ),
    skip_files: list[str] = typer.Option(
        [], "--skip", "-s", help="Files to skip during verification."
    ),
    fix: bool = typer.Option(
        False, "--fix", "-f", help="Whether to fix the headers instead of just verifying."
    ),
    project_name: Optional[str] = typer.Option(
        None, "--project", "-p", help="Name of the project to use in the header."
    ),
):
    """
    Verifies and optionally fixes qBraid headers in specified files and directories.

    """
    check_and_fix_headers(
        src_paths,
        header_type=header_type,
        skip_files=skip_files,
        fix=fix,
        project_name=project_name,
    )


if __name__ == "__main__":
    admin_app()
