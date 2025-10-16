# Copyright (c) 2024, qBraid Development Team
# All rights reserved.

"""
Module defining commands in the 'qbraid pip' namespace.

"""

import subprocess
import sys

import typer
from qbraid_core.system.exceptions import QbraidSystemError
from qbraid_core.system.executables import get_active_python_path

from qbraid_cli.handlers import handle_error
from qbraid_cli.pip.hooks import get_env_cfg_path, safe_set_include_sys_packages

pip_app = typer.Typer(help="Run pip command in active qBraid environment.", no_args_is_help=True)


@pip_app.command(
    "install", context_settings={"allow_extra_args": True, "ignore_unknown_options": True}
)
def pip_install(ctx: typer.Context):
    """
    Perform pip install action with open-ended arguments and options.

    """
    try:
        python_exe = get_active_python_path()
        cfg_path = get_env_cfg_path(python_exe)
    except QbraidSystemError:
        python_exe = sys.executable
        cfg_path = None

    safe_set_include_sys_packages(False, cfg_path)

    command = [str(python_exe), "-m", "pip", "install"] + ctx.args

    try:
        subprocess.check_call(command)
    except (subprocess.CalledProcessError, FileNotFoundError):
        handle_error(message="Failed carry-out pip command.")
    finally:
        safe_set_include_sys_packages(True, cfg_path)


if __name__ == "__main__":
    pip_app()
