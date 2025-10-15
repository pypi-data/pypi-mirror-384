# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
import os
import sys

sys.path.insert(0, os.path.abspath("../.."))

project = "ekfsm"
copyright = "2024, Klaus Popp, Felix Päßler, Jan Jansen"
author = "Klaus Popp, Felix Päßler, Jan Jansen"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",  # Auto-generate documentation from docstrings
    "sphinx.ext.autosummary",  # Generate neat summary tables
    "sphinx.ext.napoleon",  # Support for Google style docstrings
    "sphinx.ext.viewcode",  # Add links to source code
    "sphinx_autodoc_typehints",  # Auto-document type hints (optional)
    "sphinx.ext.coverage",
    "sphinx_rtd_theme",
    "sphinx.ext.intersphinx",
    "sphinx_click",
]

autodoc_typehints = "description"

templates_path = ["_templates"]
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_static_path = ["_static"]

coverage_show_missing_items = True  # Shows missing docstrings in the output
coverage_write_headline = True  # Adds a headline to the coverage report

# Automatically generate summary pages
autosummary_generate = True

html_theme = "sphinx_rtd_theme"  # or another theme of your choice

# -- General settings ------------------------------------------
master_doc = "index"  # The master toctree document

# -- Autodoc options (optional) --------------------------------
autodoc_default_options = {
    "members": True,
    "undoc-members": False,
    "private-members": False,
    "show-inheritance": True,
}

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "anytree": ("https://anytree.readthedocs.io/en/latest/", None),
}

napoleon_google_docstring = False
napoleon_numpy_docstring = True
napoleon_include_private_with_doc = True
napoleon_preprocess_types = True
napoleon_include_init_with_doc = True

# abort on error
nitpicky = True
