# Copyright 2020 - 2025 Marko Durkovic
# SPDX-License-Identifier: Apache-2.0
"""Sphinx Configuration."""

project = 'SQLs'
copyright = '2020-2024, Marko Durkovic'  # noqa: A001
author = 'Marko Durkovic'

autoapi_python_use_implicit_namespaces = True
autodoc_typehints = 'description'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx_autodoc_typehints',
    'sphinx_rtd_theme',
]

html_theme = 'sphinx_rtd_theme'
