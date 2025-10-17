# Configuration file for the Sphinx documentation builder.

# -- Path setup --------------------------------------------------------------

from datetime import datetime
import os
import sys

import solidipes as sp

# -- Project information

project = "Solidipes"
copyright = f"2023-{datetime.now().year} EPFL (École Polytechnique Fédérale de Lausanne)"
author = "Son Pham-Ba, Guillaume Anciaux"
__version__ = sp.__version__
version = __version__
release = __version__

# -- General configuration

extensions = [
    "sphinx.ext.autodoc",
    # "sphinx.ext.autosectionlabel",
    "sphinx.ext.extlinks",
    "sphinx.ext.mathjax",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.graphviz",
    "sphinx.ext.inheritance_diagram",
    "myst_parser",
]


templates_path = ["_templates"]

autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "private-members": True,
}

# -- Options for HTML output

html_theme = "sphinx_rtd_theme"
graphviz_output_format = "svg"

# -- Options for EPUB output
epub_show_urls = "footnote"


# -- Automatically run apidoc to generate rst from code
# https://github.com/readthedocs/readthedocs.org/issues/1139
def run_apidoc(_) -> None:
    from sphinx.ext.apidoc import main

    sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
    cur_dir = os.path.abspath(os.path.dirname(__file__))

    for module_dir in [
        "solidipes",
        os.path.join("plugins", "core", "solidipes_core_plugin"),
        os.path.join("plugins", "solid-mech", "solidipes_solid_mech_plugin"),
    ]:
        module = os.path.join(cur_dir, "..", module_dir)
        output = os.path.join(cur_dir, "auto_source", module_dir)
        main(["-e", "-f", "-o", output, module])


def setup(app) -> None:
    app.connect("builder-inited", run_apidoc)
