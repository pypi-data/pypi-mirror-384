# Copyright (c) 2025, qBraid Development Team
# All rights reserved.

"""
Module defining commands in the 'qbraid configure' namespace.

"""

import typer
from rich import box
from rich.console import Console
from rich.table import Table

from qbraid_cli.configure.actions import default_action

# disable pretty_exceptions_show_locals to avoid printing sensative information in the traceback
configure_app = typer.Typer(
    help="Configure qBraid CLI options.", pretty_exceptions_show_locals=False
)


@configure_app.callback(invoke_without_command=True)
def configure(ctx: typer.Context):
    """
    Prompts user for configuration values such as your qBraid API Key.
    If your config file does not exist (the default location is ~/.qbraid/qbraidrc),
    the qBraid CLI will create it for you. To keep an existing value, hit enter
    when prompted for the value. When you are prompted for information, the current
    value will be displayed in [brackets]. If the config item has no value, it be
    displayed as [None].

    """
    if ctx.invoked_subcommand is None:
        default_action()


@configure_app.command(name="set")
def configure_set(
    name: str = typer.Argument(..., help="Config name"),
    value: str = typer.Argument(..., help="Config value"),
    profile: str = typer.Option("default", "--profile", "-p", help="Profile name"),
):
    """Set configuration value in qbraidrc file."""
    # pylint: disable-next=import-outside-toplevel
    from qbraid_core.config import load_config, save_config

    config = load_config()

    if profile not in config:
        config[profile] = {}

    config[profile][name] = value

    save_config(config)
    typer.echo("Configuration updated successfully.")


@configure_app.command(name="get")
def configure_get(
    name: str = typer.Argument(..., help="Config name"),
    profile: str = typer.Option("default", "--profile", "-p", help="Profile name"),
):
    """Get configuration value from qbraidrc file."""
    # pylint: disable-next=import-outside-toplevel
    from qbraid_core.config import load_config

    config = load_config()

    if profile not in config:
        typer.echo(f"Profile '{profile}' not found in configuration.")
        raise typer.Exit(1)

    if name not in config[profile]:
        typer.echo(f"Configuration '{name}' not found in profile '{profile}'.")
        raise typer.Exit(1)

    typer.echo(config[profile][name])


@configure_app.command(name="list")
def configure_list():
    """List all configuration values in qbraidrc."""
    # pylint: disable-next=import-outside-toplevel
    from qbraid_core.config import load_config

    config = load_config()
    console = Console()
    profile = "default"

    if profile not in config:
        typer.echo("Default profile not found in configuration.")
        raise typer.Exit(1)

    if not config[profile]:
        typer.echo("No configuration values found in default profile.")
        return

    table = Table(show_edge=False, box=box.MINIMAL)
    table.add_column("Name", style="cyan")
    table.add_column("Value", style="green")

    sensitive_keys = {"api-key", "refresh-token"}

    for name, value in config[profile].items():
        if name in sensitive_keys and value:
            masked_value = f"*****{str(value)[-3:]}"
        else:
            masked_value = str(value)
        table.add_row(name, masked_value)

    console.print(table)


@configure_app.command(name="magic")
def configure_magic():
    """Enable qBraid IPython magic commands."""
    # pylint: disable-next=import-outside-toplevel
    from qbraid_core.services.environments import add_magic_config

    add_magic_config()

    console = Console()

    in_1 = (
        "[green]In [[/green][yellow]1[/yellow][green]]:[/green] [blue]%[/blue]load_ext qbraid_magic"
    )
    in_2 = "[green]In [[/green][yellow]2[/yellow][green]]:[/green] [blue]%[/blue]qbraid"

    console.print("\nSuccessfully configured qBraid IPython magic commands.\n")
    console.print("You can now use the qBraid-CLI from inside a Jupyter notebook as follows:")
    console.print(f"\n\t{in_1}\n\n\t{in_2}\n")


if __name__ == "__main__":
    configure_app()
