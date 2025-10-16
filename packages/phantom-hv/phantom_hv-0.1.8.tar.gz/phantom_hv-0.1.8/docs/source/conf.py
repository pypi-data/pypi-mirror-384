# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "phantom-hv"
copyright = "2024, Felix Werner"
author = "Felix Werner"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.linkcode",
]

autosummary_generate = True

templates_path = []
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_static_path = []
html_title = "phantom-hv"
html_theme = "furo"
html_theme_options = {
    "source_repository": "https://github.com/fwerner/phantom-hv/",
    "source_branch": "main",
    "source_directory": "docs/source/",
}

# -- Options for autodoc -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html#configuration

# Automatically extract typehints when specified and place them in
# descriptions of the relevant function/method.
autodoc_typehints = "description"

# Don't show class signature with the class' name.
autodoc_class_signature = "separated"

# -- Options for sphinx.ext.linkcode -----------------------------------------
# https://www.sphinx-doc.org/en/master/usage/extensions/linkcode.html

def linkcode_resolve(domain, info):
    if domain != 'py' or not info['module']:
        return None

    root = "blob/main/src/"
    module = info['module']
    if module.count(".") < 2:
        filename = f"{module.replace('.', '/')}/__init__.py"
    else:
        filename = f"{module.replace('.', '/')}.py"

    return f"{html_theme_options['source_repository']}{root}{filename}"
