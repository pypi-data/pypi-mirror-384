# utilities

"""
Package with various utils i.e. VB regex translation, CLI logging, file handling, ...

Set of submodules contains:

- submodule for converting  Microsoft VB /COM type regular expression to Python regular expression
- submodule with utilities to log CLI calls of Python scripts
- submodule with utilities for file handling
- submodule with wrapper for basic GUI functions for various GUI frameworks
- submodule with various utilities - read config file with standard parser, set up standard logger object ...

Raises:
    ImportError: import error if implementation is not available for platform
"""


# ruff and mypy per file settings
#
# empty lines
# ruff: noqa: E302, E303
# naming conventions
# ruff: noqa: N801, N802, N803, N806, N812, N813, N815, N816, N818, N999
#
# disable mypy errors
# mypy: disable-error-code = "assignment"

# fmt: off


# version determination

# original Hatchlor version
# from importlib.metadata import PackageNotFoundError, version
# try:
#     __version__ = version('{{ cookiecutter.project_slug }}')
# except PackageNotFoundError:  # pragma: no cover
#     __version__ = 'unknown'
# finally:
#     del version, PackageNotFoundError

# latest import requirement for hatch-vcs-footgun-example
from utils_mystuff.version import __version__


from .logger_CLI import *
from .utils_filehandling import *
from .utils_GUI import *
from .utils_various import *
from .convert_regex import *
