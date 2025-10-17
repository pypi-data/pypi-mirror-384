"""
Rebrain - Transform chat history into structured memory graphs.

A system for ingesting, synthesizing, and retrieving personal cognition
from chat exports using dual vector+graph storage.
"""

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("rebrain")
except PackageNotFoundError:
    # Package not installed, likely in development
    __version__ = "0.0.0.dev0"

__author__ = "Yasin Salimibeni"

__all__ = []

