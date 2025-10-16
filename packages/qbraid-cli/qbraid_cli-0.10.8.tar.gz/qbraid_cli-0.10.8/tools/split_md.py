# Copyright (c) 2024, qBraid Development Team
# All rights reserved.

"""
Script for splitting a markdown (md) file into
multiple files based on sections.

"""

import os
import pathlib
import re
import sys


def adjust_markdown_headers(file_path: str) -> None:
    """
    Adjusts the Markdown headers in a file:
    - Changes headers starting with '##' to start with '#'
    - Changes headers starting with '###' to start with '##'
    - Removes surrounding backticks from headers of any level.
    - Leaves headers starting with '#' unchanged.

    Args:
        file_path (str): The path to the Markdown file to be modified.

    Returns:
        None: This function does not return any value and modifies the file in-place.
    """
    with open(file_path, "r", encoding="utf-8") as file:
        lines = file.readlines()

    with open(file_path, "w", encoding="utf-8") as file:
        for line in lines:
            # Process headers starting with '###'
            if line.startswith("###"):
                line = re.sub(r"^###\s*`?(.*?)`?\s*$", "## \\1", line) + "\n"
            # Process headers starting with '##'
            elif line.startswith("##"):
                line = re.sub(r"^##\s*`?(.*?)`?\s*$", "# \\1", line) + "\n"
            # Process headers starting with '#'
            elif line.startswith("#"):
                line = re.sub(r"^#\s*`?(.*?)`?\s*$", "# \\1", line) + "\n"

            # Write the processed line back to the file
            file.write(line)


def split_markdown_file_simple(file_path: str) -> None:
    """
    Splits a Markdown file into multiple files based on sections starting with '##'.
    Each section is saved into a new file named after the section title, with spaces
    replaced by underscores and all characters converted to lowercase.

    Args:
        file_path (str): The path to the Markdown file to be split.

    Returns:
        None: This function does not return any value.

    Note:
        This function assumes that section titles start with '## ', and that there are
        no nested sections within these level 2 sections.
    """
    directory = os.path.dirname(file_path)

    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()

    # Regex to match sections starting with '## '
    section_regex = re.compile(r"^\s*# ([^#].+?)\s*$", re.MULTILINE)

    # Find all sections and their positions
    sections = [
        (match.group(1).strip(), match.start()) for match in section_regex.finditer(content)
    ]

    # Include the end of the file as a splitting point
    sections.append(("END_OF_FILE", len(content)))

    for i in range(len(sections) - 1):
        # Extract section title and positions
        section_title, start_pos = sections[i]
        end_pos = sections[i + 1][1]

        # Extract section content
        section_content = content[start_pos:end_pos].strip() + "\n"

        # Generate a new filename based on the section title
        new_filename = os.path.join(
            directory, f"{section_title.replace(' ', '_').lower().strip('`')}.md"
        )

        with open(new_filename, "w", encoding="utf-8") as new_file:
            new_file.write(section_content)


def markdown_to_mdx(file_path: str) -> None:
    """
    Transforms the first '#' header in a Markdown file and the next non-empty line
    into MDX frontmatter. Changes the file extension from .md to .mdx.

    Args:
        file_path (str): The path to the Markdown file to be transformed.

    Returns:
        None: This function does not return any value and modifies the file,
              saving it with a new extension.
    """
    with open(file_path, "r", encoding="utf-8") as file:
        lines = file.readlines()

    title = None
    description = None
    new_lines = []
    found_title = False
    skip_next_empty = False

    for _, line in enumerate(lines):
        stripped_line = line.strip()
        if not found_title and stripped_line.startswith("# "):
            # Remove the '#' and leading space to extract the title
            title = stripped_line[2:]
            found_title = True
            skip_next_empty = True
            continue  # Skip adding this line

        if found_title and skip_next_empty:
            if stripped_line == "":
                continue  # Skip empty lines immediately after the title

            # The first non-empty line after the title is taken as the description
            description = stripped_line
            skip_next_empty = False  # Reset skipping
            # Insert the frontmatter
            new_lines.extend(
                ["---\n", f"title: {title}\n", f"description: {description}\n", "---\n"]
            )
            continue

        line = line.replace("&#x27;", "'")

        if pathlib.Path(file_path).name == "qbraid_files.md":
            line = line.replace(str(pathlib.Path.cwd()), "None")

        new_lines.append(line)

    # Construct the new file path with .mdx extension
    mdx_file_path = os.path.splitext(file_path)[0] + ".mdx"

    # Write the modified content to the new file
    with open(mdx_file_path, "w", encoding="utf-8") as file:
        file.writelines(new_lines)

    # remove the original .md file
    os.remove(file_path)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python split_md.py <filename>")
        sys.exit(1)

    filename = sys.argv[1]

    if not filename.endswith(".md"):
        print("The file must have a .md extension")
        sys.exit(1)

    if not os.path.isfile(filename):
        print(f"File '{filename}' does not exist")
        sys.exit(1)

    try:
        adjust_markdown_headers(filename)
        split_markdown_file_simple(filename)
    except IOError as e:
        print(f"Error processing file {filename}: {e}")
        sys.exit(1)

    docs_dir = os.path.dirname(filename)
    for iterfile in os.listdir(docs_dir):
        full_path = os.path.join(docs_dir, iterfile)
        if full_path.endswith(".md"):
            markdown_to_mdx(full_path)
