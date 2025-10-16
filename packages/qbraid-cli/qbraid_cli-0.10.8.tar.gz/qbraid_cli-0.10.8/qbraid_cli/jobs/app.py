# Copyright (c) 2024, qBraid Development Team
# All rights reserved.

"""
Module defining commands in the 'qbraid jobs' namespace.

"""

from typing import Any, Callable

import typer
from rich.console import Console

from qbraid_cli.handlers import handle_error, print_formatted_data, run_progress_task
from qbraid_cli.jobs.toggle_braket import disable_braket, enable_braket
from qbraid_cli.jobs.validation import handle_jobs_state, run_progress_get_state, validate_library

jobs_app = typer.Typer(help="Manage qBraid quantum jobs.", no_args_is_help=True)


@jobs_app.command(name="enable")
def jobs_enable(
    library: str = typer.Argument(
        ..., help="Software library with quantum jobs support.", callback=validate_library
    ),
    auto_confirm: bool = typer.Option(
        False, "--yes", "-y", help="Automatically answer 'yes' to all prompts"
    ),
) -> None:
    """Enable qBraid Quantum Jobs."""

    def enable_action():
        if library == "braket":
            enable_braket(auto_confirm=auto_confirm)
        else:
            raise RuntimeError(f"Unsupported device library: '{library}'.")

    handle_jobs_state(library, "enable", enable_action)


@jobs_app.command(name="disable")
def jobs_disable(
    library: str = typer.Argument(
        ..., help="Software library with quantum jobs support.", callback=validate_library
    ),
    auto_confirm: bool = typer.Option(
        False, "--yes", "-y", help="Automatically answer 'yes' to all prompts"
    ),
) -> None:
    """Disable qBraid Quantum Jobs."""

    def disable_action():
        if library == "braket":
            disable_braket(auto_confirm=auto_confirm)
        else:
            raise RuntimeError(f"Unsupported device library: '{library}'.")

    handle_jobs_state(library, "disable", disable_action)


@jobs_app.command(name="state")
def jobs_state(
    library: str = typer.Argument(
        default=None,
        help="Optional: Specify a software library with quantum jobs support to check its status.",
        callback=validate_library,
    ),
) -> None:
    """Display the state of qBraid Quantum Jobs for the current environment."""
    result: tuple[str, dict[str, tuple[bool, bool]]] = run_progress_get_state(library)
    python_exe, state_values = result
    state_values = dict(sorted(state_values.items()))

    console = Console()
    header_1, header_2 = "Library", "State"
    max_lib_length = max((len(lib) for lib in state_values.keys()), default=len(header_1))
    padding = max_lib_length + 9

    output = ""
    for lib, (installed, enabled) in state_values.items():
        state_str = (
            "[green]enabled"
            if enabled and installed
            else "[red]disabled" if installed else "[grey70]unavailable"
        )
        output += f"{lib:<{padding-1}} {state_str}\n"

    console.print(f"Executable: {python_exe}")
    console.print(f"\n{header_1:<{padding}}{header_2}", style="bold")
    console.print(output)


@jobs_app.command(name="list")
def jobs_list(
    limit: int = typer.Option(
        10, "--limit", "-l", help="Limit the maximum number of results returned"
    ),
) -> None:
    """List qBraid Quantum Jobs."""

    def import_jobs() -> tuple[Any, Callable]:
        from qbraid_core.services.quantum import QuantumClient, process_job_data

        client = QuantumClient()

        return client, process_job_data

    result: tuple[Any, Callable] = run_progress_task(import_jobs)
    client, process_job_data = result
    raw_data = client.search_jobs(query={"resultsPerPage": limit, "page": 0})
    job_data, msg = process_job_data(raw_data)

    longest_job_id = max(len(item[0]) for item in job_data)
    spacing = longest_job_id + 5
    try:
        console = Console()
        header_1 = "Job ID"
        header_2 = "Submitted"
        header_3 = "Status"
        console.print(f"[bold]{header_1.ljust(spacing)}{header_2.ljust(36)}{header_3}[/bold]")
        for job_id, submitted, status in job_data:
            if status == "COMPLETED":
                status_color = "green"
            elif status in ["FAILED", "CANCELLED"]:
                status_color = "red"
            elif status in [
                "INITIALIZING",
                "INITIALIZED",
                "CREATED",
                "QUEUED",
                "VALIDATING",
                "RUNNING",
            ]:
                status_color = "blue"
            else:
                status_color = "grey"
            console.print(
                f"{job_id.ljust(spacing)}{submitted.ljust(35)}",
                f"[{status_color}]{status}[/{status_color}]",
            )

        console.print(f"\n{msg}", style="italic", justify="left")

    except Exception:  # pylint: disable=broad-exception-caught
        handle_error(message="Failed to fetch quantum jobs.")


@jobs_app.command(name="get")
def jobs_get(
    job_id: str = typer.Argument(..., help="The ID of the job to get."),
    fmt: bool = typer.Option(
        True, "--no-fmt", help="Disable rich console formatting (output raw data)"
    ),
) -> None:
    """Get a qBraid Quantum Job."""

    def get_job():
        from qbraid_core.services.quantum import QuantumClient

        client = QuantumClient()
        return client.get_job(job_id)

    data: dict[str, Any] = run_progress_task(get_job)

    print_formatted_data(data, fmt)


if __name__ == "__main__":
    jobs_app()
