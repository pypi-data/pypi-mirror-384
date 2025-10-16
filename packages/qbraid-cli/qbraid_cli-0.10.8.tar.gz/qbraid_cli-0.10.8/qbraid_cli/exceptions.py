# Copyright (c) 2024, qBraid Development Team
# All rights reserved.

"""
Module defining custom exceptions for the qBraid CLI.

"""

from typing import Optional

DEFAULT_ERROR_MESSAGE = (
    "An unexpected error occurred while processing your qBraid CLI command. "
    "Please check your input and try again. If the problem persists, "
    "visit https://github.com/qBraid/qBraid-Lab/issues to file a bug report."
)


class QbraidException(Exception):
    """Custom exception class for qBraid CLI errors."""

    def __init__(self, message: Optional[str] = None):
        if message is None:
            message = DEFAULT_ERROR_MESSAGE
        super().__init__(message)
