# Copyright (c) 2024, qBraid Development Team
# All rights reserved.

"""
Module for validating command arguments for qBraid Quantum Jobs.

"""

import sys
from typing import Any, Callable, Optional

import typer
from rich.console import Console

from qbraid_cli.handlers import handle_error, run_progress_task, validate_item

LEGACY_ARGS: dict[str, str] = {
    "amazon_braket": "braket",
    "aws_braket": "braket",
}


def validate_library(value: str) -> str:
    """Validate quantum jobs library."""
    # pylint:disable-next=import-outside-toplevel
    from qbraid_core.services.quantum.proxy import SUPPORTED_QJOB_LIBS

    qjobs_libs = list(SUPPORTED_QJOB_LIBS.keys())

    if value in LEGACY_ARGS:
        old_value = value
        value = LEGACY_ARGS[value]

        console = Console()
        console.print(
            f"[red]DeprecationWarning:[/red] Argument '{old_value}' "
            f"is deprecated. Use '{value}' instead.\n"
        )

    return validate_item(value, qjobs_libs, "Library")


def get_state(library: Optional[str] = None) -> tuple[str, dict[str, tuple[bool, bool]]]:
    """Get the state of qBraid Quantum Jobs for the specified library."""
    from qbraid_core.services.quantum import QuantumClient

    jobs_state = QuantumClient.qbraid_jobs_state(device_lib=library)

    python_exe: str = jobs_state.get("exe", sys.executable)
    libs_state: dict[str, Any] = jobs_state.get("libs", {})

    state_values = {
        lib: (state["supported"], state["enabled"]) for lib, state in libs_state.items()
    }

    return python_exe, state_values


def run_progress_get_state(
    library: Optional[str] = None,
) -> tuple[str, dict[str, tuple[bool, bool]]]:
    """Run get state function with rich progress UI."""
    return run_progress_task(
        get_state,
        library,
        description="Collecting package metadata...",
        error_message=f"Failed to collect {library} package metadata.",
    )


def handle_jobs_state(
    library: str,
    action: str,  # 'enable' or 'disable'
    action_callback: Callable[[], None],
) -> None:
    """Handle the common logic for enabling or disabling qBraid Quantum Jobs."""
    _, state_values = run_progress_get_state(library)
    installed, enabled = state_values[library]

    if not installed:
        handle_error(
            message=f"{library} not installed."
        )  # TODO: Provide command to install library?
    if (enabled and action == "enable") or (not enabled and action == "disable"):
        action_color = "green" if enabled else "red"
        console = Console()
        console.print(
            f"\nqBraid quantum jobs already [bold {action_color}]{action}d[/bold {action_color}] "
            f"for [magenta]{library}[/magenta].\n\nCheck the state of all quantum jobs "
            "libraries in this environment with: \n\n\t$ qbraid jobs state\n"
        )
        raise typer.Exit()

    action_callback()  # Perform the specific enable/disable action
