# Copyright (c) 2024, qBraid Development Team
# All rights reserved.

"""
Module defining commands in the 'qbraid kernels' namespace.

"""

import typer
from rich.console import Console

from qbraid_cli.handlers import handle_error

kernels_app = typer.Typer(help="Manage qBraid kernels.", no_args_is_help=True)


@kernels_app.command(name="list")
def kernels_list():
    """List all available kernels."""
    from qbraid_core.services.environments.kernels import get_all_kernels

    console = Console()
    # Get the list of kernelspecs
    kernelspecs: dict = get_all_kernels()

    if len(kernelspecs) == 0:
        console.print("No qBraid kernels are active.")
        console.print("\nUse 'qbraid kernels add' to add a new kernel.")
        return

    longest_kernel_name = max(len(kernel_name) for kernel_name in kernelspecs)
    spacing = longest_kernel_name + 10

    output_lines = []
    output_lines.append("# qbraid kernels:")
    output_lines.append("#")
    output_lines.append("")

    # Ensure 'python3' kernel is printed first if it exists
    default_kernel_name = "python3"
    python3_kernel_info = kernelspecs.pop(default_kernel_name, None)
    if python3_kernel_info:
        line = f"{default_kernel_name.ljust(spacing)}{python3_kernel_info['resource_dir']}"
        output_lines.append(line)
    # print rest of the kernels
    for kernel_name, kernel_info in sorted(kernelspecs.items()):
        line = f"{kernel_name.ljust(spacing)}{kernel_info['resource_dir']}"
        output_lines.append(line)

    final_output = "\n".join(output_lines)

    console.print(final_output)


@kernels_app.command(name="add")
def kernels_add(
    environment: str = typer.Argument(
        ..., help="Name of environment for which to add ipykernel. Values from 'qbraid envs list'."
    ),
):
    """Add a kernel."""
    from qbraid_core.services.environments.kernels import add_kernels

    try:
        add_kernels(environment)
    except ValueError:
        handle_error(
            message="Failed to add kernel(s). Please verify that the environment exists.",
            include_traceback=True,
        )

    console = Console()
    console.print(f"\nSuccessfully added '{environment}' kernel(s).", highlight=False)


@kernels_app.command(name="remove")
def kernels_remove(
    environment: str = typer.Argument(
        ...,
        help=("Name of environment for which to remove ipykernel. Values from 'qbraid envs list'."),
    ),
):
    """Remove a kernel."""
    from qbraid_core.services.environments.kernels import remove_kernels

    try:
        remove_kernels(environment)
    except ValueError:
        handle_error(
            message="Failed to remove kernel(s). Please verify that the environment exists.",
            include_traceback=True,
        )

    console = Console()
    console.print(f"\nSuccessfully removed '{environment}' kernel(s).", highlight=False)


if __name__ == "__main__":
    kernels_app()
