# configuration file for sphinx documentation

import os
import sys

sys.path.insert(0, os.path.abspath("../src"))

# project information
project = "fastalloc"
copyright = "2025, Eshan Roy"
author = "Eshan Roy"
release = "0.1.0"

# general configuration
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "myst_parser",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# html output
html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]

# autodoc settings
autodoc_default_options = {
    "members": True,
    "member-order": "bysource",
    "special-members": "__init__",
    "undoc-members": True,
    "exclude-members": "__weakref__",
}

# intersphinx
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}

# napoleon settings
napoleon_google_docstring = True
napoleon_numpy_docstring = True

# myst settings
myst_enable_extensions = [
    "colon_fence",
    "deflist",
]
