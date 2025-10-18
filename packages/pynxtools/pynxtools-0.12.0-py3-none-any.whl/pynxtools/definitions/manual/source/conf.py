# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

import datetime
import os
import sys

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
# add the abs path to the custom extension for collecting the contributor variables from the rst files
sys.path.insert(0, os.path.abspath("../../../dev_tools/ext"))

# -- Project information -----------------------------------------------------

project = 'NeXus-FAIRmat'
author = 'The FAIRmat consortium, a member of the German National Research Data Infrastructure (NFDI)'
copyright = u'2022-{}, {}'.format(datetime.datetime.now().year, author)
description = u'Proposal of NeXus expansion for FAIRmat data'

# The full version, including alpha/beta/rc tags
version = "unknown NXDL version"
release = "unknown NXDL release"
nxdl_version = open("../../NXDL_VERSION").read().strip()
if nxdl_version is not None:
    version = nxdl_version.split(".")[0]
    release = nxdl_version


# -- General configuration ---------------------------------------------------

# https://github.com/nexusformat/definitions/issues/659#issuecomment-577438319
needs_sphinx = '2.5'

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx_toolbox.collapse",
    "sphinx.ext.mathjax",
    "sphinx.ext.ifconfig",
    "sphinx.ext.viewcode",
    "sphinx.ext.githubpages",
    "sphinx.ext.todo",
    "sphinx_tabs.tabs",
    "contrib_ext",
    "chios.bolditalic",
    "sphinx_gallery.gen_gallery",
    "sphinx_comments",
]


# Show `.. todo` directives in the output
# todo_include_todos = True

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
html_theme = 'alabaster'
# html_theme = 'sphinxdoc'
# html_theme = 'sphinx_rtd_theme'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]

# Add extra files
html_extra_path = ['CNAME']
html_logo = 'img/FAIRmat_new.png'

if html_theme== 'sphinx_rtd_theme':
    html_theme_options = {
        'logo_only': False,
        'collapse_navigation': True,
        'sticky_navigation': True,
        'navigation_depth': 4,
        'includehidden': True,
        'titles_only': False
    }
    def setup(app):
        app.add_css_file('to_rtd.css')
        app.add_css_file('details_summary_hide.css')
elif html_theme== 'alabaster': # Alabaster allows a very high degree of control form Sphinx conf.py
    html_sidebars = {
    '**': [
        'about.html',
        'navigation.html',
        'localtoc.html',
        'relations.html',
        'sourcelink.html',
        'searchbox.html',
        'google_search.html'
        ],
    }
    html_theme_options = {
        'body_text_align': 'justify',
        'logo_name': True,
        'github_button': True,
        'github_type': 'watch',
        'github_repo': 'nexus_definitions',
        'github_user': 'FAIRmat-NFDI',
        'github_count': 'false', # We don't get the cute counter baloon if we want to point to the branch
        'sidebar_width': '300px',
        'body_max_width': 'auto',
        'page_width': 'auto',
        'font_size': '12pt',
        'font_family': 'Arial',
        'description': 'Proposal of NeXus expansion for FAIRmat data.',
        'show_powered_by': True,
        'sidebar_header': '#ffffff',
        'sidebar_hr': '#ffffff',
        'sidebar_link': '#ffffff',
        'sidebar_list': '#ffffff',
        'sidebar_link_underscore': '#ffffff',
        'sidebar_text': '#ffffff'
    }
    def setup(app):
        app.add_css_file('to_alabaster.css')
        app.add_css_file('details_summary_hide.css')
else:
    html_sidebars = {
    '**': [
        'localtoc.html',
        'relations.html',
        'sourcelink.html',
        'searchbox.html',
        'google_search.html'
        ],
    }
    def setup(app):
        app.add_css_file('details_summary_hide.css')


# The name of an image file (within the static path) to use as favicon of the
# docs.  This file should be a Windows icon file (.ico) being 16x16 or 32x32
# pixels large.
html_favicon = "../../../common/favicon.ico"

# Output file base name for HTML help builder.
htmlhelp_basename = "NeXusManualdoc"

comments_config = {
    "hypothesis": True
}
html_contexthtml_context = {
    "css_files": [
        "_static/bespoke.css",  # custom CSS styling
        "_static/bolditalic.css",  # bolditalic styling
    ],
}

# -- Options for Latex output -------------------------------------------------
latex_elements = {
    'maxlistdepth': 25, # some application definitions are deeply nested
    'preamble': r'''
    \usepackage{amsbsy}
    \listfiles
    \DeclareUnicodeCharacter{1F517}{X}
    \DeclareUnicodeCharacter{2906}{<=}
    \DeclareUnicodeCharacter{394}{$\Delta$}
    \DeclareUnicodeCharacter{2206}{$\Delta$}
    \DeclareUnicodeCharacter{1F517}{X}
    \DeclareUnicodeCharacter{2906}{<=}
    \listfiles'''
}

# -- Options the gallery -------------------------------------------------
sphinx_gallery_conf = {
    "examples_dirs": [
        "../../galleries/nxdata",
    ],  # paths with .py files that generate plots
    "gallery_dirs": [
        "classes/base_classes/data",
    ],  # paths where to save gallery generated output
    "download_all_examples": False,  # disable download buttons
    "write_computation_times": False,  # disable computation time display
    "show_signature": False,  # disable signature
}

# -- Inject Git commit information for substitution --------------------------

import subprocess

def run_git_cmd(*args):
    try:
        out = subprocess.check_output(('git',) + args)
        return out.decode().strip()
    except subprocess.SubprocessError:
        return 'unknown'

commit_hash = run_git_cmd('rev-parse', '--short', 'HEAD')
commit_time = run_git_cmd('log', '-1', '--format=%cd', '--date=iso')

rst_epilog = f"""
.. |commit_hash| replace:: {commit_hash}
.. |commit_time| replace:: {commit_time}
"""
