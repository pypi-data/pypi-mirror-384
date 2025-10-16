# Copyright (c) 2024, qBraid Development Team
# All rights reserved.

# pylint: disable=too-many-branches,too-many-statements

"""
Script to verify qBraid copyright file headers

"""

import datetime
import os
import warnings
from enum import Enum
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from qbraid_cli.handlers import handle_error

CURR_YEAR = datetime.datetime.now().year
PREV_YEAR = CURR_YEAR - 1

COMMENT_MARKER = {
    ".py": "#",
    ".js": "//",
    ".ts": "//",
}

VALID_EXTS = tuple(COMMENT_MARKER.keys())


class HeaderType(Enum):
    """Type of header to use."""

    default = "default"  # pylint: disable=invalid-name
    gpl = "gpl"  # pylint: disable=invalid-name
    apache = "apache"  # pylint: disable=invalid-name
    mit = "mit"  # pylint: disable=invalid-name


DEFAULT_HEADER = f"""# Copyright (c) {CURR_YEAR}, qBraid Development Team
# All rights reserved.
"""

DEFAULT_HEADER_GPL = f"""# Copyright (C) {CURR_YEAR} qBraid
#
# This file is part of {{project_name}}
#
# {{project_name_start}} is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for {{project_name}}, as per Section 15 of the GPL v3.
"""

DEFAULT_HEADER_APACHE = f"""# Copyright {CURR_YEAR} qBraid
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""

DEFAULT_HEADER_MIT = f"""# MIT License
#
# Copyright (c) {CURR_YEAR} qBraid
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""

HEADER_TYPES = {
    HeaderType.default: DEFAULT_HEADER,
    HeaderType.gpl: DEFAULT_HEADER_GPL,
    HeaderType.apache: DEFAULT_HEADER_APACHE,
    HeaderType.mit: DEFAULT_HEADER_MIT,
}


def get_formatted_header(header_type: HeaderType, project_name: Optional[str] = None) -> str:
    """Get the formatted header based on the header type

    Args:
        header_type (str): The type of header to use.
        project_name (str): The name of the project to use in the header.

    Returns:
        str: The formatted header
    """

    header = HEADER_TYPES[header_type]
    if header_type == HeaderType.gpl:
        if project_name is None:
            handle_error("ValueError", "Project name is required for GPL header")

        if project_name.split(" ")[0].lower() == "the":
            project_name = project_name[:1].lower() + project_name[1:]
            project_name_start = project_name[:1].upper() + project_name[1:]
        else:
            project_name_start = project_name
        return header.format(project_name=project_name, project_name_start=project_name_start)

    if project_name is not None:
        warnings.warn(f"\nProject name is not used for header type '{header_type}'.", UserWarning)

    return header


def _get_comment_marker(file_path: str, default: Optional[str] = None) -> str:
    file_ext = Path(file_path).suffix
    return COMMENT_MARKER.get(file_ext, default)


def check_and_fix_headers(
    src_paths: list[str],
    header_type: HeaderType = HeaderType.default,
    skip_files: Optional[list[str]] = None,
    fix: bool = False,
    project_name: Optional[str] = None,
) -> None:
    """Script to add or verify qBraid copyright file headers"""
    try:
        header = get_formatted_header(header_type, project_name)
    except KeyError:
        members = HeaderType._member_names_  # pylint: disable=no-member,protected-access
        handle_error(
            error_type="ValueError",
            message=(f"Invalid header type: {HEADER_TYPES}. Expected one of {members}"),
        )

    for path in src_paths:
        if not os.path.exists(path):
            handle_error(error_type="FileNotFoundError", message=f"Path '{path}' does not exist.")

    header_prev_year = header.replace(str(CURR_YEAR), str(PREV_YEAR))

    skip_files = skip_files or []

    failed_headers = []
    fixed_headers = []

    console = Console()

    def should_skip(file_path: str, content: str) -> bool:
        if file_path in skip_files:
            return True

        if os.path.basename(file_path) == "__init__.py":
            return not content.strip()

        comment_marker = _get_comment_marker(file_path)
        skip_header_tag = f"{comment_marker} qbraid: skip-header"
        line_number = 0

        for line in content.splitlines():
            line_number += 1
            if 5 <= line_number <= 30 and skip_header_tag in line:
                return True
            if line_number > 30:
                break

        return False

    def replace_or_add_header(file_path: str, fix: bool = False) -> None:
        with open(file_path, "r", encoding="ISO-8859-1") as f:
            content = f.read()

        comment_marker = _get_comment_marker(file_path)

        # This finds the start of the actual content after skipping initial whitespace and comments.
        lines = content.splitlines()
        first_non_comment_line_index = next(
            (i for i, line in enumerate(lines) if not line.strip().startswith(comment_marker)), None
        )

        # Prepare the content by stripping leading and trailing whitespace and separating into lines
        actual_content = (
            "\n".join(lines[first_non_comment_line_index:]).strip()
            if first_non_comment_line_index is not None
            else ""
        )

        updated_header = header.replace("#", comment_marker)
        updated_prev_header = header_prev_year.replace("#", comment_marker)

        # Check if the content already starts with the header or if the file should be skipped
        if (
            content.lstrip().startswith(updated_header)
            or content.lstrip().startswith(updated_prev_header)
            or should_skip(file_path, content)
        ):
            return

        if not fix:
            failed_headers.append(file_path)
        else:
            # Form the new content by combining the header, one blank line, and the actual content
            new_content = updated_header.strip() + "\n\n" + actual_content + "\n"
            with open(file_path, "w", encoding="ISO-8859-1") as f:
                f.write(new_content)
            fixed_headers.append(file_path)

    def process_files_in_directory(directory: str, fix: bool = False) -> int:
        count = 0
        if not os.path.isdir(directory):
            return count
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith(VALID_EXTS):
                    file_path = os.path.join(root, file)
                    replace_or_add_header(file_path, fix)
                    count += 1
        return count

    checked = 0
    for item in src_paths:
        if os.path.isdir(item):
            checked += process_files_in_directory(item, fix)
        elif os.path.isfile(item) and item.endswith(VALID_EXTS):
            replace_or_add_header(item, fix)
            checked += 1
        else:
            if not os.path.isfile(item):
                handle_error(
                    error_type="FileNotFoundError", message=f"Path '{item}' does not exist."
                )

    if checked == 0:
        console.print(f"[bold]No {VALID_EXTS} files present. Nothing to do[/bold] 😴")
        raise typer.Exit(0)

    if not fix:
        if failed_headers:
            for file in failed_headers:
                console.print(f"[bold]would fix {file}[/bold]")
            num_failed = len(failed_headers)
            num_passed = checked - num_failed
            s1, s2 = ("", "s") if num_failed == 1 else ("s", "")
            s_passed = "" if num_passed == 1 else "s"
            console.print("[bold]\nOh no![/bold] 💥 💔 💥")
            if num_passed > 0:
                punc = ", "
                passed_msg = f"[blue]{num_passed}[/blue] file{s_passed} would be left unchanged."
            else:
                punc = "."
                passed_msg = ""

            failed_msg = f"[bold][blue]{num_failed}[/blue] file{s1} need{s2} updating{punc}[/bold]"
            console.print(f"{failed_msg}{passed_msg}")
            raise typer.Exit(1)

        s_checked = "" if checked == 1 else "s"
        console.print("[bold]All done![/bold] ✨ 🚀 ✨")
        console.print(f"[blue]{checked}[/blue] file{s_checked} would be left unchanged.")
        raise typer.Exit(0)

    for file in fixed_headers:
        console.print(f"[bold]fixed {file}[/bold]")
    num_fixed = len(fixed_headers)
    num_ok = checked - num_fixed
    s_fixed = "" if num_fixed == 1 else "s"
    s_ok = "" if num_ok == 1 else "s"
    console.print("\n[bold]All done![/bold] ✨ 🚀 ✨")
    if num_ok > 0:
        punc = ", "
        unchanged_msg = f"[blue]{num_ok}[/blue] file{s_ok} left unchanged."
    else:
        punc = "."
        unchanged_msg = ""

    if num_fixed > 0:
        fixed_msg = f"[bold][blue]{num_fixed}[/blue] file{s_fixed} fixed{punc}[/bold]"
    else:
        fixed_msg = ""

    console.print(f"{fixed_msg}{unchanged_msg}")
    raise typer.Exit(0)
