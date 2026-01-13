"""
lstring - Lazy string implementation for Python

This module provides a wrapper around the _lstring C extension,
exposing the L class for lazy string operations.
"""

from .lstring import L, CharClass, get_optimize_threshold, set_optimize_threshold

def get_include():
    import os

    return os.path.join(os.path.dirname(__file__), "include")

__all__ = ['L', 'CharClass', 'get_optimize_threshold', 'set_optimize_threshold', 'get_include']
