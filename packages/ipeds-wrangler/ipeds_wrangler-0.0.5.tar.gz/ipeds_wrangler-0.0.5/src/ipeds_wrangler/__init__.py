# ipeds_wrangler/__init__.py

"""
ipeds_wrangler - a Python package for wrangling IPEDS data
"""

from .download_ipeds_databases import download_databases

__all__ = ['download_ipeds_databases']

def __version__():
    """Return the package version."""
    return "0.0.5"

def describe():
    """Print the package description."""
    description = (
        "ipeds_wrangler\n"
        "version: {}\n"
        "a Python package for wrangling IPEDS data"
    ).format(__version__())
    print(description)