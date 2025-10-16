# Copyright (c) 2024, qBraid Development Team
# All rights reserved.

"""
Script for getting/bumping the next pre-release version.

"""

import pathlib
import re
import sys

from qbraid_core.system.versions import get_prelease_version


def replace_version_format(v: str) -> str:
    """
    Replace the version format from "x.y.z-abc.def" to "x.y.zabcdef".

    Args:
        v (str): The version string to transform.

    Returns:
        str: The transformed version string.
    """
    pattern = r"-(\w+)\.(\d+)"
    new_version = re.sub(pattern, r"\1\2", v)
    return new_version


if __name__ == "__main__":
    package_name = sys.argv[1]
    root = pathlib.Path(__file__).parent.parent.resolve()
    version = get_prelease_version(root, package_name)
    formatted_version = replace_version_format(version)
    print(formatted_version)
