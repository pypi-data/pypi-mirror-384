"""Top-level package for imsi."""

__author__ = """CCCma Technical Development Team"""
__email__ = ""

from importlib.metadata import version, PackageNotFoundError
import pathlib

try:
    __version__ = version("imsi")
except PackageNotFoundError:
    # fallback (e.g. during local dev before install)
    __version__ = "unknown"
