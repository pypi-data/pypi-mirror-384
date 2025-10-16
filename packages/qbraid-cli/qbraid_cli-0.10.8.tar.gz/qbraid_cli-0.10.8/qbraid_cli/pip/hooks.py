# Copyright (c) 2024, qBraid Development Team
# All rights reserved.

"""
Module defining pre- and post-command hooks for the 'qbraid pip' namespace.

"""

import sys
from pathlib import Path
from typing import Optional, Union

from qbraid_core.services.environments import get_default_envs_paths
from qbraid_core.system.executables import python_paths_equivalent
from qbraid_core.system.packages import (
    extract_include_sys_site_pkgs_value,
    set_include_sys_site_pkgs_value,
)


def safe_set_include_sys_packages(value: bool, file_path: Optional[Union[str, Path]]) -> None:
    """Set include-system-site-packages value safely"""
    if not file_path:
        return None

    try:
        set_include_sys_site_pkgs_value(value, file_path)
    except Exception:  # pylint: disable=broad-exception-caught
        pass

    return None


def find_matching_prefix(python_executable: Path, path_list: list[Path]) -> Optional[Path]:
    """
    Finds and returns the first path in the list that is a prefix of the Python executable path.

    Args:
        python_executable (Path): The path to the Python executable.
        path_list (list[Path]): A list of paths to check against the Python executable path.

    Returns:
        Optional[Path]: The first matching path that is a prefix of the Python executable path,
                        or None if no match is found.
    """
    python_executable_str = str(python_executable.resolve())
    for path in path_list:
        if python_executable_str.startswith(str(path.resolve())):
            return path
    return None


def get_env_cfg_path(python_exe: Path) -> Optional[Path]:
    """Get the path to the pyvenv.cfg file."""
    is_sys_python = python_paths_equivalent(python_exe, sys.executable)

    if is_sys_python:
        return None

    all_envs_paths = get_default_envs_paths()

    env_path = find_matching_prefix(python_exe, all_envs_paths)

    if not env_path:
        return None

    cfg_path = env_path / "pyvenv.cfg"

    should_flip = extract_include_sys_site_pkgs_value(cfg_path)

    if should_flip:
        return cfg_path

    return None
