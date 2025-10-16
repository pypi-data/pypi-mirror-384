# Copyright (c) 2024, qBraid Development Team
# All rights reserved.

"""
Script for splitting a reStructuredText (rst) file into
multiple files based on sections.

"""

import os
import re
import sys


def apply_text_transformations(file_path: str) -> None:
    """
    Applies multiple text transformations to a .rst file, including replacing
    sequences of dashes and carets with equals and dashes respectively, removing
    backticks from section titles followed by section lines, replacing escaped
    colons with unescaped colons, and condensing multiple newlines into a single newline.

    This function performs all replacements in one pass and writes the transformed
    content back to the original file.

    Args:
        file_path (str): The path to the .rst file to be transformed.

    Returns:
        None: This function does not return any value.
    """
    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()

    # Replace dashes and carets with equals and dashes respectively in one pass
    content = re.sub(r"---+", lambda m: "=" * len(m.group()), content)
    content = re.sub(r"\^\^\^+", lambda m: "-" * len(m.group()), content)

    # Remove backticks from section titles if the next line is a section line
    content = re.sub(r"^``(.*?)``\n([=+\-^]+)$", r"\1\n\2", content, flags=re.MULTILINE)

    content = content.replace("\\ :", ":")
    content = content.replace("\n\n\n", "\n\n")

    # Add a backslash directly before '*args' preceded by any amount of whitespace
    content = re.sub(r"(^\s*)(\*args)", r"\1\\\2", content, flags=re.MULTILINE)

    with open(file_path, "w", encoding="utf-8") as file:
        file.write(content)


def split_rst_file_simple(file_path: str) -> None:
    """
    Splits a reStructuredText (rst) file into multiple files based on sections underlined
    by three or more '=' characters. Each section is saved into a new file named after
    the section title, with spaces replaced by underscores and all characters converted
    to lowercase.

    Args:
        file_path (str): The path to the rst file to be split.

    Returns:
        None: This function does not return any value.

    Note:
        This function assumes that section titles are immediately followed by a line of
        '=' characters and that there are no nested sections within these sections.
    """
    directory = os.path.dirname(file_path)

    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()

    # Regex to match sections underlined by three or more '=' characters
    section_regex = re.compile(r"^(.*\n)(=+)$", re.MULTILINE)

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
        section_content = content[start_pos:end_pos].strip()

        # Generate a new filename based on the section title
        new_filename = os.path.join(directory, f"{section_title.replace(' ', '_').lower()}.rst")

        with open(new_filename, "w", encoding="utf-8") as new_file:
            new_file.write(section_content)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python split_rst.py <filename>")
        sys.exit(1)

    filename = sys.argv[1]

    if not filename.endswith(".rst"):
        print("The file must have a .rst extension")
        sys.exit(1)

    if not os.path.isfile(filename):
        print(f"File '{filename}' does not exist")
        sys.exit(1)

    try:
        apply_text_transformations(filename)
        split_rst_file_simple(filename)
    except IOError as e:
        print(f"Error processing file {filename}: {e}")
        sys.exit(1)
