"""Core plugin for Solidipes with essential modular components"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("solidipes_core_plugin")
except PackageNotFoundError:
    pass
