# Copyright (c) 2024, qBraid Development Team
# All rights reserved.

"""
Unit tests for the `qbraid_cli.envs.app` module's `activate` command.

"""
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from qbraid_cli.envs.app import envs_app

runner = CliRunner(mix_stderr=False)

MOCK_API_RETURN_OBJ = {
    "description": "This is a test qBraid environment for demonstration purposes.",
    "logo": "test_s3_url",
    "slug": "test_env_slug",
    "displayName": "test_env",
    "kernelName": "sample_kernel",
    "name": "test_env",
    "packagesInImage": {"numpy>=1.21.1", "openqasm3~=0.5.0", "qiskit", "cirq==1.0.0"},
    "prompt": "sample_prompt",
    "tags": ["test", "qbraid", "environment"],
}


def test_invalid_name_raises_error():
    """Test that an invalid name raises an error."""
    result = runner.invoke(
        envs_app,
        ["create", "--name", "invalid large name for environment", "--description", "test"],
    )
    assert result.exit_code == 2
    assert "Invalid environment name " in result.stderr


# we mock the usage path of the method NOT its definition path
@patch("qbraid_cli.envs.app.run_progress_task")
def test_correct_yaml_parse(mock_run_progress_task):
    """Test that the correct YAML file is parsed correctly."""

    mock_run_progress_task.side_effect = [
        (MOCK_API_RETURN_OBJ, None),
        (Path("path/to/test_env"), "3.8"),
        None,
        None,
    ]
    yaml_file = "resources/envs/correct.yaml"
    file_path = Path(__file__).resolve().parent.parent / yaml_file
    result = runner.invoke(envs_app, ["create", "--file", file_path])
    assert result.exit_code == 0
    expected_outputs = [
        "Successfully created qBraid environment: test_env",
        "name: test_env",
        "description: This is a test qBraid environment for demonstration purposes.",
        "tags: ['test', 'qbraid', 'environment']",
        "slug: test_env_slug",
        "shellPrompt: sample_prompt",
        "kernelName: sample_kernel",
        f"location: {Path('path/to/test_env/test_env_slug')}",
        "version: 3.8",
    ]
    for output in expected_outputs:
        assert output in result.stdout


def test_invalid_yaml_file_raises_error():
    """Test that an invalid YAML file raises an error."""
    yaml_file = "resources/envs/incorrect.yaml"
    file_path = Path(__file__).resolve().parent.parent / yaml_file
    result = runner.invoke(envs_app, ["create", "--file", file_path])

    assert result.exit_code == 1
    assert "Invalid YAML data" in result.stderr


def test_no_name_no_file_raises_error():
    """Test that providing neither a name nor a file raises an error."""
    result = runner.invoke(envs_app, ["create"])
    assert result.exit_code == 1
    assert (
        "Must provide either --name and --description or --file while creating an environment"
        in result.stderr
    )


def test_name_with_file_raises_error():
    """Test that providing both a name and a file raises an error."""
    result = runner.invoke(
        envs_app,
        [
            "create",
            "--name",
            "test_env",
            "--description",
            "test",
            "--file",
            "resources/envs/correct.yaml",
        ],
    )
    assert result.exit_code == 1
    assert (
        "Cannot use --file with --name or --description while creating an environment"
        in result.stderr
    )
