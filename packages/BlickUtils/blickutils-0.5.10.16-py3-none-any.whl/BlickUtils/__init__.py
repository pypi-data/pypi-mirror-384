"""
blick_utils - A collection of utility functions
"""

__version__ = "0.5.10"

from .core import BlickUtils

# Dynamically expose all static methods:
for name in dir(BlickUtils):
    attr = getattr(BlickUtils, name)
    if callable(attr):
        globals()[name] = attr
