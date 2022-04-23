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
from pkg_resources import get_distribution

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

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "numpydoc",
    "myst_parser",
    "sphinx.ext.autosummary",
    "sphinx.ext.autosectionlabel",
    "matplotlib.sphinxext.plot_directive",
    "sphinx.ext.intersphinx",  # links to numpy, scipy ... docs
    "sphinx.ext.viewcode",
    "sphinx.ext.doctest",
    "sphinx.ext.coverage",
    "sphinx.ext.extlinks",  # define roles for links
    "sphinx_toggleprompt",  # toggle `>>>`
    "sphinx.ext.graphviz",
    "sphinx.ext.inheritance_diagram",
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.

exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "tests"]


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
html_theme = "furo"  # "sphinx_rtd_theme"

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = "sphinx"
# pygments_dark_style = "monokai"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]

# Include Markdown parser
# source_parsers = {
#    '.md': 'recommonmark.parser.CommonMarkParser',
# }
source_suffix = [".rst", ".md"]

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


# -- Plots -------------------------------------------------------------------

plot_pre_code = """
import warnings
import numpy as np
import matplotlib.pyplot as plt
import lattpy as lp
np.random.seed(0)
"""

doctest_global_setup = plot_pre_code  # make doctests consistent
doctest_global_cleanup = """
try:
    plt.close()  # close any open figures
except:
    pass
"""

plot_include_source = True
plot_html_show_source_link = False
plot_formats = [("png", 100), "pdf"]

phi = (math.sqrt(5) + 1) / 2

plot_rcparams = {
    "font.size": 8,
    "axes.titlesize": 8,
    "axes.labelsize": 8,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "legend.fontsize": 8,
    "figure.figsize": (3 * phi, 3),
    "figure.subplot.bottom": 0.2,
    "figure.subplot.left": 0.2,
    "figure.subplot.right": 0.9,
    "figure.subplot.top": 0.85,
    "figure.subplot.wspace": 0.4,
    "text.usetex": False,
}


# -- Intersphinx -------------------------------------------------------------

# taken from https://gist.github.com/bskinn/0e164963428d4b51017cebdb6cda5209
intersphinx_mapping = {
    "python": (r"https://docs.python.org", None),
    "numpy": (r"https://docs.scipy.org/doc/numpy/", None),
    "np": (r"https://docs.scipy.org/doc/numpy/", None),
    "matplotlib": (r"https://matplotlib.org/", None),
}


# -- Graphviz options --------------------------------------------------------

graphviz_output_format = "svg"
inheritance_graph_attrs = dict(rankdir="LR", size='""')
