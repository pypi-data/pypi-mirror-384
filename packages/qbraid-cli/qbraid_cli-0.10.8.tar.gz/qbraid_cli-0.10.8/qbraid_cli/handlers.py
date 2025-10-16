# Copyright (c) 2024, qBraid Development Team
# All rights reserved.

"""
Module providing application support utilities, including abstractions for error handling
and executing operations with progress tracking within the qBraid CLI.

"""

import os
import traceback
from pathlib import Path
from time import sleep
from typing import Any, Callable, Optional, Union

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TaskID, TextColumn

from .exceptions import DEFAULT_ERROR_MESSAGE, QbraidException


def _should_display_progress():
    """Whether to display rich progress UI."""
    return os.getenv("QBRAID_CLI_SHOW_PROGRESS", "true").lower() in ["true", "1", "t", "y", "yes"]


def _update_completed_task(
    progress: Progress, task_id: TaskID, success: bool = True, sleep_time: float = 0.15
):
    status = "Done" if success else "Failed"
    progress.update(task_id, completed=100, status=status)
    sleep(sleep_time)


def handle_error(
    error_type: Optional[str] = None, message: Optional[str] = None, include_traceback: bool = True
) -> None:
    """Generic CLI error handling helper function.

    This function handles errors by printing a styled error message to stderr and optionally
    including a traceback. It then exits the application with a non-zero status code, indicating
    an error.

    Args:
        error_type (Optional[str]): The type of the error to be displayed. Defaults to "Error" if
                                    not specified.
        message (Optional[str]): The error message to be displayed. If not specified, a default
                                 error message is used.
        include_traceback (bool): If True, include the traceback of the exception in the output.
                                  Defaults to True.

    Raises:
        typer.Exit: Exits the application with a status code of 1 to indicate an error.
    """
    error_type = error_type or "Error"
    message = message or DEFAULT_ERROR_MESSAGE
    error_prefix = typer.style(f"{error_type}:", fg=typer.colors.RED, bold=True)
    full_message = f"\n{error_prefix} {message}\n"
    if include_traceback:
        tb_string = traceback.format_exc()
        # TODO: find out reason for weird traceback emitted from
        # qbraid jobs enable/disable when library not installed.
        # For now, if matches, just don't print it.
        if tb_string.strip() != "NoneType: None":
            full_message += f"\n{tb_string}"
    typer.echo(full_message, err=True)
    raise typer.Exit(code=1)


def handle_filesystem_operation(operation: Callable[[], None], path: Path) -> None:
    """
    Executes a filesystem operation with error handling.

    Args:
        operation (Callable[[], None]): The operation to be executed. This should be a callable that
                                        performs the desired filesystem operation, such as creating
                                        directories or writing files.
        path (Path): The path involved in the operation, used for error messaging.

    Raises:
        QbraidException: If a PermissionError or OSError occurs during the operation.
    """
    try:
        operation()
    except PermissionError as err:
        raise QbraidException(f"Permission denied: Unable to write to {path}.") from err
    except OSError as err:
        raise QbraidException(f"Failed to save configuration to {path}: {err.strerror}") from err


def print_formatted_data(data: Any, fmt: bool = True) -> None:
    """
    Print data with optional formatting using rich console.

    Args:
        data (Any): The data to be printed.
        fmt (bool): If True, use rich console formatting. If False, use standard print.
                   Defaults to True.
    """
    if fmt:
        console = Console()
        console.print(data)
    else:
        print(data)


def run_progress_task(
    operation: Callable[..., Any],
    *args,
    description: Optional[str] = None,
    error_message: Optional[str] = None,
    include_error_traceback: bool = True,
    **kwargs,
) -> Any:
    """
    Executes a given operation while displaying its progress.

    This function abstracts the setup and update of progress tasks, allowing for a
    uniform interface for task execution with progress tracking. It supports custom
    error messages and utilizes the rich library for console output.

    Args:
        operation (Callable[..., Any]): The operation to be executed. This can be any callable
                                        that performs the task's work.
        *args: Variable length argument list for the operation.
        description (optional, str): The description of the task to display in the progress bar.
        error_message (optional, str): Custom error message to display if the operation.
                                       fails. Defaults to None, in which case the
                                       exception's message is used.
        include_error_traceback (bool): Whether to include the traceback in the error message.
                                        Defaults to True.
        **kwargs: Arbitrary keyword arguments for the operation.

    Returns:
        Any: The result of the operation, if successful.

    Raises:
        typer.Exit: If the operation fails, after displaying the error message using typer.secho.
    """
    if not _should_display_progress():
        try:
            return operation(*args, **kwargs)
        except Exception as err:  # pylint: disable=broad-exception-caught
            custom_message = error_message if error_message else str(err)
            return handle_error(message=custom_message, include_traceback=include_error_traceback)

    console = Console()
    with Progress(
        "[progress.description]{task.description}",
        SpinnerColumn(),
        TextColumn("{task.fields[status]}"),
        console=console,
    ) as progress:
        description = description if description else "Fetching..."
        task = progress.add_task(description, status="In Progress", total=None)
        try:
            result = operation(*args, **kwargs)
            _update_completed_task(progress, task, success=True)
            return result
        except Exception as err:  # pylint: disable=broad-exception-caught
            _update_completed_task(progress, task, success=False)
            custom_message = error_message if error_message else str(err)
            return handle_error(message=custom_message, include_traceback=include_error_traceback)
        finally:
            progress.remove_task(task)


def _format_list_items(items: list[str]) -> str:
    """
    Formats a list of items as a string with values comma-separated and
    each item surrounded by single quotes

    Args:
        items (list[str]): The list of items to format.

    Returns:
        str: The formatted string.
    """
    return ", ".join(f"'{item}'" for item in items)


def validate_item(
    value: Optional[str], allowed_items: list[str], item_type: str
) -> Union[str, None]:
    """
    Generic item validation function.

    Args:
        value (optional, str): The value to validate.
        allowed_items (list[str]): A list of allowed items.
        item_type (str): A description of the item type (e.g., 'provider', 'status', 'type') for
                         error messages.

    Returns:
        Union[str, None]: The validated value, in its original case as specified in the
                          allowed_items list, or None if the value is None.

    Raises:
        typer.BadParameter: If the value is not in the allowed_items list.
    """
    if value is None:
        return None

    items_lower_to_original = {item.lower(): item for item in allowed_items}

    value_lower = value.lower()
    if value_lower not in items_lower_to_original:
        items_formatted = _format_list_items(allowed_items)
        raise typer.BadParameter(f"{item_type.capitalize()} must be one of {items_formatted}.")
    return items_lower_to_original[value_lower]
