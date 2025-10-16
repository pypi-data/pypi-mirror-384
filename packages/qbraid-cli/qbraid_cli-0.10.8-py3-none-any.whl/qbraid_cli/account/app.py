# Copyright (c) 2024, qBraid Development Team
# All rights reserved.

"""
Module defining commands in the 'qbraid user' namespace.

"""

from typing import Any

import rich
import typer

from qbraid_cli.configure.actions import QBRAID_ORG_MODEL_ENABLED
from qbraid_cli.handlers import run_progress_task

account_app = typer.Typer(help="Manage qBraid account.", no_args_is_help=True)


@account_app.command(name="credits")
def account_credits():
    """Get number of qBraid credits remaining."""

    def get_credits() -> float:
        from qbraid_core import QbraidClient

        client = QbraidClient()
        return client.user_credits_value()

    qbraid_credits: float = run_progress_task(get_credits)
    typer.secho(
        f"{typer.style('qBraid credits remaining:')} "
        f"{typer.style(f'{qbraid_credits:.4f}', fg=typer.colors.MAGENTA, bold=True)}",
        nl=True,  # Ensure a newline after output (default is True)
    )
    rich.print("\nFor more information, visit: https://docs.qbraid.com/home/pricing#credits")


@account_app.command(name="info")
def account_info():
    """Get qBraid account (user) metadata."""

    def get_user() -> dict[str, Any]:
        from qbraid_core import QbraidSession

        session = QbraidSession()
        user = session.get_user()
        personal_info: dict = user.get("personalInformation", {})
        metadata = {
            "_id": user.get("_id"),
            "userName": user.get("userName"),
            "email": user.get("email"),
            "joinedDate": user.get("createdAt", "Unknown"),
            "activePlan": user.get("activePlan", "") or "Free",
            "role": personal_info.get("role", "") or "guest",
        }
        if QBRAID_ORG_MODEL_ENABLED:
            metadata["organization"] = personal_info.get("organization", "") or "qbraid"

        return metadata

    info = run_progress_task(get_user)
    rich.print(info)


if __name__ == "__main__":
    account_app()
