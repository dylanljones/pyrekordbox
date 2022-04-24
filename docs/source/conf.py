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
import os
import sys
import math

sys.path.insert(0, os.path.abspath("../.."))

import pyrekordbox


# -- Project information -----------------------------------------------------

project = "pyrekordbox"
copyright = "2022, Dylan Jones"
author = "Dylan L. Jones"
release = pyrekordbox.__version__
version = release
for sp in "abcfr":
    version = version.split(sp)[0]

# -- General configuration ---------------------------------------------------

# If your documentation needs a minimal Sphinx version, state it here.
needs_sphinx = "4.0"

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "numpydoc",
    "myst_parser",
    "numpydoc",
    "sphinx_copybutton",
    "sphinx.ext.napoleon",
    "sphinx.ext.autosummary",
    "sphinx.ext.autosectionlabel",
    "matplotlib.sphinxext.plot_directive",
    "sphinx.ext.intersphinx",  # links to numpy, scipy ... docs
    "sphinx.ext.coverage",
    "sphinx.ext.extlinks",  # define roles for links
]

# If you need extensions of a certain version or higher, list them here.
needs_extensions = {"myst_parser": "0.13.7"}

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.

exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "tests"]

# The suffix(es) of source filenames.
# You can specify multiple suffix as a list of string:
source_suffix = [".rst", ".md"]

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
html_theme = "furo"

# The name of the Pygments (syntax highlighting) style to use.
# pygments_style = "sphinx"
pygments_dark_style = "monokai"

# We need headers to be linkable to so ask MyST-Parser to autogenerate anchor IDs for
# headers up to and including level 3.
myst_heading_anchors = 3

# Prettier support formatting some MyST syntax but not all, so let's disable the
# unsupported yet still enabled by default ones.
myst_disable_syntax = [
    "colon_fence",
    "myst_block_break",
    "myst_line_comment",
    "math_block",
]


# Don't show type hints
autodoc_typehints = "none"

# Preserve order
autodoc_member_order = "bysource"


# -- Apidoc ------------------------------------------------------------------

add_module_names = True


# -- Autosummary -------------------------------------------------------------

autosummary_generate = True
# autosummary_imported_members = True


# -- Numpy extension ---------------------------------------------------------

numpydoc_use_plots = True
# numpydoc_xref_param_type = True
# numpydoc_xref_ignore = "all"  # not working...
numpydoc_show_class_members = False


# -- Intersphinx -------------------------------------------------------------

# taken from https://gist.github.com/bskinn/0e164963428d4b51017cebdb6cda5209
intersphinx_mapping = {
    "python": (r"https://docs.python.org", None),
    "numpy": (r"https://docs.scipy.org/doc/numpy/", None),
    "np": (r"https://docs.scipy.org/doc/numpy/", None),
    "matplotlib": (r"https://matplotlib.org/", None),
}


# -- Auto-run sphinx-apidoc --------------------------------------------------

# def run_apidoc(_):
#     from sphinx.ext.apidoc import main
#     import os
#     import sys
#     sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
#     cur_dir = os.path.abspath(os.path.dirname(__file__))
#     proj_dir = os.path.dirname(os.path.dirname(cur_dir))
#     doc_dir = os.path.join(proj_dir, "docs")
#     output_path = os.path.join(doc_dir, "source", "generated")
#     module = os.path.join(proj_dir, "pyrekordbox")
#     exclude = os.path.join(module, "tests")
#     template_dir = os.path.join(doc_dir, "source", "_templates", "apidoc")
#     main(["-fMeT", "-o", output_path, module, exclude, "--templatedir", template_dir])
#
#
# def setup(app):
#     app.connect('builder-inited', run_apidoc)
