# Copyright (c) 2024, qBraid Development Team
# All rights reserved.

"""
Module defining commands in the 'qbraid devices' namespace.

"""

from typing import Any, Callable, Optional

import typer
from rich.console import Console

from qbraid_cli.devices.validation import validate_provider, validate_status, validate_type
from qbraid_cli.handlers import print_formatted_data, run_progress_task

devices_app = typer.Typer(help="Manage qBraid quantum devices.", no_args_is_help=True)


@devices_app.command(name="list")
def devices_list(  # pylint: disable=too-many-branches
    status: Optional[str] = typer.Option(
        None, "--status", "-s", help="'ONLINE'|'OFFLINE'|'RETIRED'", callback=validate_status
    ),
    device_type: Optional[str] = typer.Option(
        None, "--type", "-t", help="'QPU'|'SIMULATOR'", callback=validate_type
    ),
    provider: Optional[str] = typer.Option(
        None,
        "--provider",
        "-p",
        help=(
            "'AWS'|'IBM'|'IonQ'|'Rigetti'|'OQC'|'QuEra'|'IQM'|"
            "'NEC'|'qBraid'|'Azure'|'Pasqal'|'Quantinuum'|'Equal1'"
        ),
        callback=validate_provider,
    ),
) -> None:
    """List qBraid quantum devices."""
    filters = {}
    if status:
        filters["status"] = status
    if device_type:
        filters["type"] = "Simulator" if device_type == "SIMULATOR" else device_type
    if provider:
        filters["provider"] = provider

    def import_devices() -> tuple[Any, Callable]:
        from qbraid_core.services.quantum import QuantumClient, process_device_data

        client = QuantumClient()

        return client, process_device_data

    result: tuple[Callable, Callable] = run_progress_task(import_devices)
    client, process_device_data = result
    raw_data = client.search_devices(filters)
    device_data, msg = process_device_data(raw_data)

    console = Console()
    header_1 = "Provider"
    header_2 = "Device Name"
    header_3 = "ID"
    header_4 = "Status"
    console.print(
        f"[bold]{header_1.ljust(12)}{header_2.ljust(35)}{header_3.ljust(41)}{header_4}[/bold]"
    )
    for device_provider, device_name, device_id, device_status in device_data:
        if device_status == "ONLINE":
            status_color = "green"
        elif device_status == "OFFLINE":
            status_color = "red"
        else:
            status_color = "grey"
        console.print(
            f"{device_provider.ljust(12)}{device_name.ljust(35)}{device_id.ljust(40)}",
            f"[{status_color}]{device_status}[/{status_color}]",
        )
    console.print(f"\n{msg}", style="italic", justify="left")


@devices_app.command(name="get")
def devices_get(
    device_id: str = typer.Argument(..., help="The ID of the device to get."),
    fmt: bool = typer.Option(
        True, "--no-fmt", help="Disable rich console formatting (output raw data)"
    ),
) -> None:
    """Get a qBraid quantum device."""

    def get_device():
        from qbraid_core.services.quantum import QuantumClient

        client = QuantumClient()
        return client.get_device(device_id)

    data: dict[str, Any] = run_progress_task(get_device)

    print_formatted_data(data, fmt)


if __name__ == "__main__":
    devices_app()
