# Copyright (c) 2024, qBraid Development Team
# All rights reserved.

"""
Configurations for pytest including remote test marker and command-line option.

"""
import os

import pytest


def pytest_addoption(parser):
    """Adds custom remote testing command-line option to pytest."""
    parser.addoption(
        "--remote",
        action="store",
        default=None,
        help="Run tests that interface with remote, credentialed services: true or false",
    )


def pytest_collection_modifyitems(config, items):
    """Skip tests marked with `remote` if remote tests are disabled."""
    remote_option = config.getoption("--remote")
    if remote_option is None:
        remote_option = os.getenv("QBRAID_RUN_REMOTE_TESTS", "True").lower() == "true"
    else:
        remote_option = remote_option.lower() == "true"

    if not remote_option:
        skip_remote = pytest.mark.skip(reason="Remote tests are disabled.")
        for item in items:
            if "remote" in item.keywords:
                item.add_marker(skip_remote)
