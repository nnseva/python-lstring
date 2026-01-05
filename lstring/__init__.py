"""
lstring - Lazy string implementation for Python

This module provides a wrapper around the _lstring C extension,
exposing the L class and re submodule for lazy string operations.
"""

from .lstring import L, CharClass, get_optimize_threshold, set_optimize_threshold

__all__ = ['L', 'CharClass', 'get_optimize_threshold', 'set_optimize_threshold']
