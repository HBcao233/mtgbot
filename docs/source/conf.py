# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import sys
import os

sys.path.insert(0, os.path.abspath('../../'))


project = 'mtgbot'
copyright = '2024, HBcao233'
author = 'HBcao233'
release = '0.1.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = []

templates_path = ['_templates']
exclude_patterns = []

language = 'zh'

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output


extensions = [
  'sphinx.ext.autodoc', 
  'sphinx.ext.githubpages',
  'sphinx.ext.napoleon',
]

html_theme = 'sphinx_rtd_theme'

html_static_path = ['_static']

locale_dirs = ['locale']
