# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html


# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "Snip-python"
copyright = "2024, Sebastian B. Mohr"
author = "Sebastian B. Mohr"

master_doc = "index"
language = "en"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration


templates_path = ["_templates"]
exclude_patterns = []


extensions = [
    "sphinx.ext.intersphinx",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx_copybutton",
    "sphinx_inline_tabs",
    "sphinxcontrib.typer",
    "sphinx.ext.napoleon",
    # "myst_parser",
    "myst_nb",
]
autosummary_generate = True  # Turn on sphinx.ext.autosummary
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "jsonschema": ("https://python-jsonschema.readthedocs.io/en/stable", None),
}
nb_execution_mode = "off"
myst_enable_extensions = [
    "colon_fence",
    "deflist",
]


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "furo"
html_static_path = ["_static"]
html_theme_options = {
    "light_logo": "favicon-128x128-light.png",
    "dark_logo": "favicon-128x128-dark.png",
    "light_css_variables": {
        "color-brand-primary": "#2f3992",
        "color-brand-content": "#dee2e6",
    },
    "dark_css_variables": {
        "color-brand-primary": "#2f3992",
        "color-brand-content": "#dee2e6",
    },
    # Sources for editing
    "source_view_link": "https://gitlab.gwdg.de/irp/snip/-/tree/main/packages/python/docs/{filename}",
    "footer_icons": [
        {
            "name": "GitLab",
            "url": "https://gitlab.gwdg.de/irp/snip",
            "html": """
                <svg stroke="currentColor" fill="none" stroke-width="2" viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round" height="200px" width="200px" xmlns="http://www.w3.org/2000/svg"><path d="M22.65 14.39L12 22.13 1.35 14.39a.84.84 0 0 1-.3-.94l1.22-3.78 2.44-7.51A.42.42 0 0 1 4.82 2a.43.43 0 0 1 .58 0 .42.42 0 0 1 .11.18l2.44 7.49h8.1l2.44-7.51A.42.42 0 0 1 18.6 2a.43.43 0 0 1 .58 0 .42.42 0 0 1 .11.18l2.44 7.51L23 13.45a.84.84 0 0 1-.35.94z"></path></svg>
            """,
            "class": "",
        },
    ],
}
html_css_files = [
    "custom.css",
]
