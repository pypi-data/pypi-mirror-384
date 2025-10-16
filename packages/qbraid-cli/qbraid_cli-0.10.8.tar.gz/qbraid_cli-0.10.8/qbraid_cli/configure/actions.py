# Copyright (c) 2024, qBraid Development Team
# All rights reserved.

"""
Module defining actions invoked by 'qbraid configure' command(s).

"""

import configparser
import re
from copy import deepcopy
from typing import Optional

import typer
from qbraid_core.config import (
    DEFAULT_CONFIG_SECTION,
    DEFAULT_ENDPOINT_URL,
    DEFAULT_ORGANIZATION,
    DEFAULT_WORKSPACE,
    USER_CONFIG_PATH,
    load_config,
    save_config,
)
from rich.console import Console

from qbraid_cli.handlers import handle_filesystem_operation

QBRAID_ORG_MODEL_ENABLED = False  # Set to True if organization/workspace model is enabled


def validate_input(key: str, value: str) -> str:
    """Validate the user input based on the key.

    Args:
        key (str): The configuration key
        value (str): The user input value

    Returns:
        str: The validated value

    Raises:
        typer.BadParameter: If the value is invalid
    """
    value = value.strip()

    if key == "url":
        if not re.match(r"^https?://\S+$", value):
            raise typer.BadParameter("Invalid URL format.")
    elif key == "email":
        if not re.match(r"^\S+@\S+\.\S+$", value):
            raise typer.BadParameter("Invalid email format.")
    elif key == "api-key":
        if not re.match(r"^[a-zA-Z0-9]+$", value):
            raise typer.BadParameter("Invalid API key format.")
    return value


def prompt_for_config(
    config: configparser.ConfigParser,
    section: str,
    key: str,
    default_values: Optional[dict[str, str]] = None,
) -> str:
    """Prompt the user for a configuration setting, showing the current value as default."""
    default_values = default_values or {}
    current_value = config.get(section, key, fallback=default_values.get(key, ""))
    display_value = "None" if not current_value else current_value
    hide_input = False
    show_default = True

    if section == DEFAULT_CONFIG_SECTION:
        if key == "url":
            return current_value

        if key == "api-key":
            if current_value:
                display_value = "*" * len(current_value[:-4]) + current_value[-4:]
            hide_input = True
            show_default = False

    new_value = typer.prompt(
        f"Enter {key}", default=display_value, show_default=show_default, hide_input=hide_input
    ).strip()

    if new_value == display_value:
        return current_value

    return validate_input(key, new_value)


def default_action(section: str = DEFAULT_CONFIG_SECTION):
    """Configure qBraid CLI options."""
    config = load_config()
    original_config = deepcopy(config)

    if section not in config:
        config[section] = {}

    default_values = {
        "url": DEFAULT_ENDPOINT_URL,
    }
    if QBRAID_ORG_MODEL_ENABLED:
        default_values["organization"] = DEFAULT_ORGANIZATION
        default_values["workspace"] = DEFAULT_WORKSPACE

    config[section]["url"] = prompt_for_config(config, section, "url", default_values)
    config[section]["api-key"] = prompt_for_config(config, section, "api-key", default_values)

    if QBRAID_ORG_MODEL_ENABLED:
        config[section]["organization"] = prompt_for_config(
            config, section, "organization", default_values
        )
        config[section]["workspace"] = prompt_for_config(
            config, section, "workspace", default_values
        )

    for key in list(config[section]):
        if not config[section][key]:
            del config[section][key]

    console = Console()
    if config == original_config:
        console.print("\n[bold grey70]Configuration saved, unchanged.")
    else:

        def _save_config():
            save_config(config)

        handle_filesystem_operation(_save_config, USER_CONFIG_PATH)
        console.print("\n[bold green]Configuration updated successfully.")
