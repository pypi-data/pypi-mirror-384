# Copyright (c) 2024, qBraid Development Team
# All rights reserved.

"""
Module defining commands in the 'qbraid envs' namespace.

"""

import shutil
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Optional

import typer
from qbraid_core.services.environments.schema import EnvironmentConfig
from rich.console import Console

from qbraid_cli.envs.create import create_qbraid_env_assets, create_venv
from qbraid_cli.envs.data_handling import get_envs_data as installed_envs_data
from qbraid_cli.envs.data_handling import validate_env_name
from qbraid_cli.handlers import QbraidException, handle_error, run_progress_task

if TYPE_CHECKING:
    from qbraid_core.services.environments.client import EnvironmentManagerClient as EMC

envs_app = typer.Typer(help="Manage qBraid environments.", no_args_is_help=True)


@envs_app.command(name="create")
def envs_create(  # pylint: disable=too-many-statements
    name: str = typer.Option(None, "--name", "-n", help="Name of the environment to create"),
    description: Optional[str] = typer.Option(
        None, "--description", "-d", help="Short description of the environment"
    ),
    file_path: str = typer.Option(
        None, "--file", "-f", help="Path to a .yml file containing the environment details"
    ),
    auto_confirm: bool = typer.Option(
        False, "--yes", "-y", help="Automatically answer 'yes' to all prompts"
    ),
) -> None:
    """Create a new qBraid environment."""
    env_description = description or ""
    if name:
        if not validate_env_name(name):
            handle_error(
                error_type="ValueError",
                include_traceback=False,
                message=f"Invalid environment name '{name}'. ",
            )

    env_details_in_cli = name is not None and env_description != ""
    env_config = None
    if env_details_in_cli and file_path:
        handle_error(
            error_type="ArgumentConflictError",
            include_traceback=False,
            message="Cannot use --file with --name or --description while creating an environment",
        )
    elif not env_details_in_cli and not file_path:
        handle_error(
            error_type="MalformedCommandError",
            include_traceback=False,
            message="Must provide either --name and --description or --file "
            "while creating an environment",
        )
    else:
        try:
            if file_path:
                env_config: EnvironmentConfig = EnvironmentConfig.from_yaml(file_path)
        except ValueError as err:
            handle_error(error_type="YamlValidationError", message=str(err))

    if not name:
        name = env_config.name

    def create_environment(*args, **kwargs) -> "tuple[dict, EMC]":
        """Create a qBraid environment."""
        from qbraid_core.services.environments.client import EnvironmentManagerClient

        client = EnvironmentManagerClient()
        return client.create_environment(*args, **kwargs), client

    def gather_local_data() -> tuple[Path, str]:
        """Gather environment data and return the slug."""
        from qbraid_core.services.environments import get_default_envs_paths

        env_path = get_default_envs_paths()[0]

        result = subprocess.run(
            [sys.executable, "--version"],
            capture_output=True,
            text=True,
            check=True,
        )

        python_version = result.stdout or result.stderr

        return env_path, python_version

    if not env_config:
        env_config = EnvironmentConfig(
            name=name,
            description=env_description,
        )

    create_env_out: tuple[dict, EMC] = run_progress_task(
        create_environment,
        env_config,
        description="Validating request...",
        error_message="Failed to create qBraid environment",
    )

    environment, emc = create_env_out
    slug = environment.get("slug")

    local_data_out: tuple[Path, str] = run_progress_task(
        gather_local_data,
        description="Solving environment...",
        error_message="Failed to create qBraid environment",
    )

    env_path, python_version = local_data_out

    env_config.name = environment.get("displayName")
    env_config.shell_prompt = environment.get("prompt")
    env_config.description = environment.get("description")
    env_config.tags = environment.get("tags")
    env_config.kernel_name = environment.get("kernelName")
    env_config.python_version = python_version

    slug_path = env_path / slug
    description = "None" if description == "" else description

    typer.echo("## qBraid Metadata ##\n")
    typer.echo(f"  name: {env_config.name}")
    typer.echo(f"  description: {env_config.description}")
    typer.echo(f"  tags: {env_config.tags}")
    typer.echo(f"  slug: {slug}")
    typer.echo(f"  shellPrompt: {env_config.shell_prompt}")
    typer.echo(f"  kernelName: {env_config.kernel_name}")

    typer.echo("\n\n## Environment Plan ##\n")
    typer.echo(f"  location: {slug_path}")
    typer.echo(f"  version: {python_version}\n")

    user_confirmation = auto_confirm or typer.confirm("Proceed", default=True)
    typer.echo("")
    if not user_confirmation:
        emc.delete_environment(slug)
        typer.echo("qBraidSystemExit: Exiting.")
        raise typer.Exit()

    run_progress_task(
        create_qbraid_env_assets,
        slug,
        slug_path,
        env_config,
        description="Generating qBraid assets...",
        error_message="Failed to create qBraid environment",
    )

    run_progress_task(
        create_venv,
        slug_path,
        env_config.shell_prompt,
        description="Creating virtual environment...",
        error_message="Failed to create qBraid environment",
    )

    console = Console()
    console.print(
        f"[bold green]Successfully created qBraid environment: "
        f"[/bold green][bold magenta]{name}[/bold magenta]\n"
    )
    typer.echo("# To activate this environment, use")
    typer.echo("#")
    typer.echo(f"#     $ qbraid envs activate {name}")
    typer.echo("#")
    typer.echo("# To deactivate an active environment, use")
    typer.echo("#")
    typer.echo("#     $ deactivate")


@envs_app.command(name="remove")
def envs_remove(
    name: str = typer.Option(..., "-n", "--name", help="Name of the environment to remove"),
    auto_confirm: bool = typer.Option(
        False, "--yes", "-y", help="Automatically answer 'yes' to all prompts"
    ),
) -> None:
    """Delete a qBraid environment."""

    def delete_environment(slug: str) -> None:
        """Delete a qBraid environment."""
        from qbraid_core.services.environments.client import EnvironmentManagerClient

        emc = EnvironmentManagerClient()
        emc.delete_environment(slug)

    def gather_local_data(env_name: str) -> tuple[Path, str]:
        """Get environment path and slug from name (alias)."""
        installed, aliases = installed_envs_data()
        for alias, slug in aliases.items():
            if alias == env_name:
                path = installed[slug]

                return path, slug

        raise QbraidException(f"Environment '{name}' not found.")

    slug_path, slug = gather_local_data(name)

    confirmation_message = (
        f"⚠️  Warning: You are about to delete the environment '{name}' "
        f"located at '{slug_path}'.\n"
        "This will remove all local packages and permanently delete all "
        "of its associated qBraid environment metadata.\n"
        "This operation CANNOT be undone.\n\n"
        "Are you sure you want to continue?"
    )

    if auto_confirm or typer.confirm(confirmation_message, abort=True):
        typer.echo("")
        run_progress_task(
            delete_environment,
            slug,
            description="Deleting remote environment data...",
            error_message="Failed to delete qBraid environment",
        )

        run_progress_task(
            shutil.rmtree,
            slug_path,
            description="Deleting local environment...",
            error_message="Failed to delete qBraid environment",
        )
        typer.echo(f"Environment '{name}' successfully removed.")


@envs_app.command(name="list")
def envs_list():
    """List installed qBraid environments."""
    installed, aliases = installed_envs_data()

    console = Console()

    if len(installed) == 0:
        console.print(
            "No qBraid environments installed.\n\n"
            + "Use 'qbraid envs create' to create a new environment.",
            style="yellow",
        )
        return

    alias_path_pairs = [(alias, installed[slug_name]) for alias, slug_name in aliases.items()]
    sorted_alias_path_pairs = sorted(
        alias_path_pairs,
        key=lambda x: (x[0] != "default", str(x[1]).startswith(str(Path.home())), x[0]),
    )

    current_env_path = Path(sys.executable).parent.parent.parent

    max_alias_length = (
        max(len(str(alias)) for alias, envpath in sorted_alias_path_pairs)
        if sorted_alias_path_pairs
        else 0
    )

    output_lines = []
    output_lines.append("# qbraid environments:")
    output_lines.append("#")
    output_lines.append("")

    for alias, path in sorted_alias_path_pairs:
        mark = "*" if path == current_env_path else " "
        line = f"{alias.ljust(max_alias_length + 3)}{mark} {path}"
        output_lines.append(line)

    final_output = "\n".join(output_lines)

    console.print(final_output)


@envs_app.command(name="activate")
def envs_activate(
    name: str = typer.Argument(
        ..., help="Name of the environment. Values from 'qbraid envs list'."
    ),
):
    """Activate qBraid environment.

    NOTE: Currently only works on qBraid Lab platform, and select few other OS types.
    """
    installed, aliases = installed_envs_data()
    if name in aliases:
        venv_path: Path = installed[aliases[name]] / "pyenv"
    elif name in installed:
        venv_path: Path = installed[name] / "pyenv"
    else:
        raise typer.BadParameter(f"Environment '{name}' not found.")

    from .activate import activate_pyvenv

    activate_pyvenv(venv_path)


if __name__ == "__main__":
    envs_app()
