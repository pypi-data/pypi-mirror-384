# Copyright (c) 2024, qBraid Development Team
# All rights reserved.

"""
Module for handling data related to qBraid environments.

"""

import typer

from qbraid_cli.handlers import QbraidException


def get_envs_data(*args, **kwargs) -> dict:
    """Get data for installed environments."""
    from qbraid_core.services.environments.paths import installed_envs_data

    return installed_envs_data(*args, **kwargs)


def is_valid_env_name(value: str) -> bool:
    """Check if a given string is a valid Python environment name."""
    from qbraid_core.services.environments.validate import is_valid_env_name as is_valid

    return is_valid(value)


def validate_env_name(value: str) -> str:
    """Validate environment name."""
    if not is_valid_env_name(value):
        raise typer.BadParameter(
            f"Invalid environment name '{value}'. " "Please use a valid Python environment name."
        )
    return value


def request_delete_env(slug: str) -> str:
    """Send request to delete environment given slug."""
    from qbraid_core import QbraidSession, RequestsApiError

    session = QbraidSession()

    try:
        session.delete(f"/environments/{slug}")
    except RequestsApiError as err:
        raise QbraidException("Delete environment request failed") from err
