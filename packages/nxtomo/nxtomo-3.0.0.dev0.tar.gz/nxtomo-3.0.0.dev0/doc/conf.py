# -- Project information -----------------------------------------------------

project = "nxtomo"
copyright = "2023, ESRF"
author = "P.Paleo, H.Payno, A. Mirone, J.Lesaint"

# The full version, including alpha/beta/rc tags
release = "3.0-dev"
version = release


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosectionlabel",
    "sphinx.ext.intersphinx",
    "sphinx.ext.viewcode",
    "sphinx.ext.doctest",
    "sphinx.ext.inheritance_diagram",
    "sphinx.ext.autosummary",
    "nbsphinx",
    "sphinx_autodoc_typehints",
]

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "pydata_sphinx_theme"

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = "sphinx"

html_logo = "img/nxtomo.png"

# autosummary options
autosummary_generate = True
autosummary_imported_members = True

autodoc_default_flags = [
    "members",
    "undoc-members",
    "show-inheritance",
]


html_theme_options = {
    "icon_links": [
        {
            "name": "pypi",
            "url": "https://pypi.org/project/nxtomo",
            "icon": "_static/navbar_icons/pypi.svg",
            "type": "local",
        },
        {
            "name": "gitlab",
            "url": "https://gitlab.esrf.fr/tomotools/nxtomo",
            "icon": "_static/navbar_icons/gitlab.svg",
            "type": "local",
        },
    ],
    "show_toc_level": 1,
    "navbar_align": "left",
    "show_version_warning_banner": True,
    "navbar_start": ["navbar-logo", "version"],
    "navbar_center": ["navbar-nav"],
    "footer_start": ["copyright"],
    "footer_center": ["sphinx-version"],
}
