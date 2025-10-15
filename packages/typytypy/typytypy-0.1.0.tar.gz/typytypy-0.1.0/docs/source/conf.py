# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------
import os
import sys

from typytypy import __version__

sys.path.insert(0, os.path.abspath('../../src'))


# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'typytypy'
copyright = '2025, KitschCode'
author = 'KitscherEins'
release = __version__


# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',      # Auto-generate docs from docstrings
    'sphinx.ext.napoleon',     # Parse Google-style docstrings
    'sphinx.ext.viewcode',     # Add links to source code
    'myst_parser',             # Support for Markdown files using MyST parser
    'sphinx_copybutton',       # Enable copy button for code blocks
    'sphinx_design',           # Support responsive web components
    'sphinx_togglebutton',     # Enable dropdown feature
]

# MyST parser configuration
myst_enable_extensions = [
    "colon_fence",  # Enables ::: fences
    "deflist",      # Definition lists
    "fieldlist",    # Field lists
]

# Napoleon settings for Google-style docstrings
napoleon_google_docstring = True
napoleon_numpy_docstring = False

templates_path = ['_templates']
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'furo'

html_static_path = ['_static']

# TypyTypy logo
html_logo = '_static/images/logo/typytypy-logo-header.png'
html_favicon = '_static/images/favicon/typytypy-favicon.svg'
