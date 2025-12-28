"""
lstring - Lazy string implementation for Python

This module provides a wrapper around the _lstring C extension,
exposing the L class and re submodule for lazy string operations.
"""

from _lstring import *

__all__ = ['L', 're']
