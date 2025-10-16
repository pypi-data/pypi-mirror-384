# Copyright (c) 2024, qBraid Development Team
# All rights reserved.

"""
Module for validating command arguments for qBraid admin commands.

"""

import os

import typer

from qbraid_cli.handlers import _format_list_items


def validate_paths_exist(paths: list[str]) -> list[str]:
    """Verifies that each path in the provided list exists."""
    non_existent_paths = [path for path in paths if not os.path.exists(path)]
    if non_existent_paths:
        if len(non_existent_paths) == 1:
            raise typer.BadParameter(f"Path '{non_existent_paths[0]}' does not exist")
        raise typer.BadParameter(
            f"The following paths do not exist: {_format_list_items(non_existent_paths)}"
        )
    return paths
