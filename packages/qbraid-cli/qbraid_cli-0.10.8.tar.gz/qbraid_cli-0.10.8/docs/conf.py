# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# http://www.sphinx-doc.org/en/master/config

# -- Project information -----------------------------------------------------

project = "qBraid"
copyright = "2024, qBraid Development Team"
author = "qBraid Development Team"

import os

try:
    import tomllib

    mode = "rb"
except ImportError:
    import toml as tomllib

    mode = "r"


def cli_version():
    """Get the version from the pyproject.toml file."""
    try:
        file_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "pyproject.toml",
        )

        with open(file_path, mode) as file:
            pyproject_toml = tomllib.load(file)
            return pyproject_toml["project"]["version"]

    except (FileNotFoundError, IOError) as err:
        raise FileNotFoundError("Unable to find or read pyproject.toml") from err


# Set the version
version = cli_version()

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.viewcode",  # Hide source code link
]

# The master toctree document.
master_doc = "index"

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "*.pytest_cache", "*.ipynb_checkpoints", "*tests", "*cli/*.rst"]

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
html_theme = "sphinx_rtd_theme"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]

html_favicon = "_static/favicon.ico"
html_show_sphinx = False

html_css_files = ["style/s4defs-roles.css"]
