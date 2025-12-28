"""
lstring - Lazy string implementation for Python

This module provides a wrapper around the _lstring C extension,
exposing the L class and re submodule for lazy string operations.
"""

import _lstring


class L(_lstring.L):
    """
    Lazy string class - a Python wrapper around the C++ implementation.
    
    Inherits from _lstring.L to allow Python-level customization while
    maintaining C++ performance for core operations.
    """
    pass


# Re-export utility functions from _lstring
get_optimize_threshold = _lstring.get_optimize_threshold
set_optimize_threshold = _lstring.set_optimize_threshold


# Import re module from lstring.re
from . import re


__all__ = ['L', 're', 'get_optimize_threshold', 'set_optimize_threshold']
