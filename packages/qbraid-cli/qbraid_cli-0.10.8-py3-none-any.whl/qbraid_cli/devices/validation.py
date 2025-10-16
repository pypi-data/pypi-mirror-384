# Copyright (c) 2024, qBraid Development Team
# All rights reserved.

"""
Module for validating command arguments for qBraid devices commands.

"""

from typing import Optional, Union

from qbraid_cli.handlers import validate_item


def validate_status(value: Optional[str]) -> Union[str, None]:
    """Validate device status query parameter."""
    return validate_item(value, ["ONLINE", "OFFLINE", "RETIRED"], "Status")


def validate_type(value: Optional[str]) -> Union[str, None]:
    """Validate device type query parameter."""
    return validate_item(value, ["QPU", "SIMULATOR"], "Type")


def validate_provider(value: Optional[str]) -> Union[str, None]:
    """Validate device provider query parameter."""
    return validate_item(value, ["AWS", "IBM", "IonQ", "Rigetti", "OQC", "QuEra"], "Provider")
