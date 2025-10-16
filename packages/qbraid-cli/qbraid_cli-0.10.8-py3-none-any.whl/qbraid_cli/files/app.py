# Copyright (c) 2024, qBraid Development Team
# All rights reserved.

"""
Module defining commands in the 'qbraid files' namespace.

"""

from pathlib import Path
from typing import Any

import rich
import typer

from qbraid_cli.handlers import handle_error, run_progress_task

files_app = typer.Typer(help="Manage qBraid cloud storage files.", no_args_is_help=True)


def is_file_less_than_10mb(file_path: Path) -> bool:
    """
    Check if the given file is less than 10MB in size.

    Args:
        file_path (Path): The path to the file to check.

    Returns:
        bool: True if the file is less than 10MB, False otherwise.
    """
    ten_mb = 10485760  # 10 MB in bytes (10 * 1024 * 1024)

    try:
        return file_path.stat().st_size < ten_mb
    except OSError:
        return False


@files_app.command(name="upload")
def files_upload(
    filepath: Path = typer.Argument(
        ...,
        exists=True,
        dir_okay=False,
        resolve_path=True,
        help="Local path to the file to upload.",
    ),
    namespace: str = typer.Option(
        "user",
        "--namespace",
        "-n",
        help="Target qBraid namespace for the upload.",
    ),
    object_path: str = typer.Option(
        None,
        "--object-path",
        "-p",
        help=("Target object path. " "Defaults to original filename in namespace root."),
    ),
    overwrite: bool = typer.Option(
        False,
        "--overwrite",
        "-o",
        help="Overwrite existing file if it already exists in the target location.",
    ),
):
    """Upload a local file to qBraid storage."""

    if not is_file_less_than_10mb(filepath):
        handle_error("Error", "File too large. Must be less than 10MB for direct upload.")

    def upload_file() -> dict[str, Any]:
        from qbraid_core.services.storage import FileStorageClient

        client = FileStorageClient()
        data = client.upload_file(
            filepath, namespace=namespace, object_path=object_path, overwrite=overwrite
        )
        return data

    data: dict = run_progress_task(
        upload_file, description="Uploading file...", include_error_traceback=False
    )

    rich.print("File uploaded successfully!")
    namespace = data.get("namespace")
    object_path = data.get("objectPath")

    if namespace and object_path:
        rich.print(f"\nNamespace: '{namespace}'")
        rich.print(f"Object path: '{object_path}'")


@files_app.command(name="download")
def files_download(
    object_path: str = typer.Argument(
        ...,
        help="The folder + filename describing the file to download.",
    ),
    namespace: str = typer.Option(
        "user",
        "--namespace",
        "-n",
        help="Source qBraid namespace for the download.",
    ),
    save_path: Path = typer.Option(
        Path.cwd(),
        "--save-path",
        "-s",
        resolve_path=True,
        help="Local directory to save the downloaded file.",
    ),
    overwrite: bool = typer.Option(
        False,
        "--overwrite",
        "-o",
        help="Overwrite existing file if it already exists in the target location.",
    ),
):
    """Download a file from qBraid storage."""

    def download_file() -> Path:
        from qbraid_core.services.storage import FileStorageClient

        client = FileStorageClient()
        file_path = client.download_file(
            object_path, namespace=namespace, save_path=save_path, overwrite=overwrite
        )
        return file_path

    file_path: Path = run_progress_task(
        download_file, description="Downloading file...", include_error_traceback=False
    )

    rich.print("File downloaded successfully!")
    rich.print(f"Saved to: '{str(file_path)}'")


if __name__ == "__main__":
    files_app()
