# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys
sys.path.insert(0, os.path.abspath('../../src'))


# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'orrery'
copyright = "2025, Code Choreography Limited"
author = "Tom Doel"


# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',  # Auto generate html from docstrings
    'sphinx.ext.autosummary',  # Create neat summary tables
    'sphinx.ext.intersphinx',  # Link to other project's docs (see mapping below)
    'sphinx.ext.viewcode',  # Link to the Python source code
    'sphinx_autodoc_typehints',  # Automatically document param types (less noise in class signature)
    'myst_parser',  # Process Markdown (.md) files
    'sphinx.ext.napoleon'  # Allow Google-style docstrings
]

# Mappings for sphinx.ext.intersphinx. Projects have to have Sphinx-generated doc! (.inv file)
intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
}

autosummary_generate = True  # Turn on sphinx.ext.autosummary
autoclass_content = "both"  # Add __init__ doc (ie. params) to class summaries
html_show_sourcelink = False  # Remove 'view source code' from top of page (for html, not python)
autodoc_inherit_docstrings = True  # If no docstring, inherit from base class
set_type_checking_flag = True  # Enable 'expensive' imports for sphinx_autodoc_typehints
# autodoc_typehints = "description" # Sphinx-native method. Not as good as sphinx_autodoc_typehints
add_module_names = False  # Remove namespaces from class/method signatures

templates_path = ['_templates']
source_suffix = ['.rst', '.md']
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

# Pydata theme
html_theme = "pydata_sphinx_theme"
# html_logo = "_static/logo.png"
html_theme_options = {
    "show_prev_next": False,
    "footer_end": []  # Remove theme name and version
}
html_css_files = ['pydata-custom.css']
html_show_sphinx = False

html_static_path = ['_static']

myst_footnote_transition = False
