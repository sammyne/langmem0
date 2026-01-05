import os
import sys
sys.path.insert(0, os.path.abspath('../src'))

project = 'langmem0'
copyright = '2024, langmem0 developers'
author = 'langmem0 developers'
release = '0.1.0'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx_autodoc_typehints',
]

autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'special-members': '__init__',
    'undoc-members': True,
    'exclude-members': '__weakref__'
}

html_theme = 'alabaster'
html_static_path = ['_static']
