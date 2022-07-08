# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import sphinx_book_theme
import os
import sys
sys.path.insert(0, os.path.abspath('..'))
print(f"Root dir: {sys.path[0]}")

# -- Project information -----------------------------------------------------

project = 'redengine'
copyright = '2021, Mikael Koli'
author = 'Mikael Koli'


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.doctest',
    'sphinx.ext.autodoc', 
    'sphinx.ext.coverage', 
    'sphinx.ext.napoleon',
    'sphinx_book_theme',
    'sphinx_copybutton',
]
rst_prolog = """
.. include:: <s5defs.txt>

"""

doctest_global_setup = '''
def cleanup():
    from redengine import Session
    from redengine.core.hook import clear_hooks
    Session.default_config['task_pre_exist'] = 'replace'

    clear_hooks()
    session = Session()
    session.set_as_default()
    #session.config['use_instance_naming'] = True
    
cleanup()
'''

# Extension settings

napoleon_google_docstring = True
napoleon_numpy_docstring = True

autodoc_typehints = 'none'
autodoc_member_order = 'bysource'

# Add any paths that contain templates here, relative to this directory.
#templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']
#html_sidebars = {}

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_title = "Red Engine: Advanced Scheduler"
html_theme = 'sphinx_book_theme'
html_logo = "logo.svg"
html_favicon = 'favicon.ico'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

html_css_files = [
    'css/types.css',
    'css/colors.css',
]