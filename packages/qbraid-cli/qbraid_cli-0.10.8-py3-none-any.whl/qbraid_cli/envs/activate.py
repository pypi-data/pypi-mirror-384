# Copyright (c) 2024, qBraid Development Team
# All rights reserved.

"""
Module supporting 'qbraid envs activate' command.

"""

import os
from pathlib import Path

import typer


def find_shell_rc(shell_path: str) -> str:
    """Finds an existing shell configuration file in the user's home directory."""
    if "bash" not in shell_path:
        raise ValueError(f"Unsupported shell: {shell_path}")

    possible_files = [".bashrc", ".bash_profile", ".bash_login"]

    for file_name in possible_files:
        rc_file = Path.home() / file_name
        if rc_file.exists():
            return str(rc_file)

    raise FileNotFoundError(f"No {shell_path} configuration file found in the home directory.")


def print_activate_command(venv_path: Path) -> None:
    """Prints the command to activate the virtual environment with improved formatting."""
    typer.echo("To activate this environment, use command:\n")
    if os.name == "nt":
        # Windows operating system
        activate_script = venv_path / "Scripts" / "activate"
        activate_script_ps = venv_path / "Scripts" / "Activate.ps1"
        typer.echo("\t$ " + str(activate_script))
        typer.echo("\nOr for PowerShell, use:\n")
        typer.echo("\t$ " + f"& {activate_script_ps}")
    else:
        # Unix-like operating systems (Linux/macOS)
        activate_script = venv_path / "bin" / "activate"
        typer.echo("\t$ " + f"source {activate_script}")
    typer.echo("")
    raise typer.Exit()


def activate_pyvenv(venv_path: Path):
    """Activate the virtual environment."""
    shell_path = os.environ.get("SHELL")

    if shell_path is None:
        print_activate_command(venv_path)
        return  # Return early since we can't proceed without a shell
    try:
        shell_rc = find_shell_rc(shell_path)
    except (FileNotFoundError, ValueError):
        print_activate_command(venv_path)
        return  # Return early since no suitable shell rc file was found
    bin_path = str(venv_path / "bin")

    os.system(
        f"cat {shell_rc} {bin_path}/activate > {bin_path}/activate2 && "
        f"{shell_path} --rcfile {bin_path}/activate2"
    )
