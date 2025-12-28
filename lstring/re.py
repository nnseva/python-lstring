"""
lstring.re - Regular expression module for lazy strings

This module provides Python wrappers around the _lstring.re C extension,
exposing Pattern and Match classes that can be extended in Python.
"""

import _lstring


class Pattern(_lstring.re.Pattern):
    """
    Compiled regular expression pattern - a Python wrapper around the C++ implementation.
    
    Inherits from _lstring.re.Pattern to allow Python-level customization while
    maintaining C++ performance for pattern matching operations.
    """
    pass


class Match(_lstring.re.Match):
    """
    Match object - a Python wrapper around the C++ implementation.
    
    Inherits from _lstring.re.Match to allow Python-level customization while
    maintaining C++ performance for match operations.
    """
    pass


# Re-export module-level functions from _lstring.re
def compile(pattern, flags=0, Match=None):
    """
    Compile a regular expression pattern.
    
    Args:
        pattern: Pattern string (str or lstring.L)
        flags: Optional regex flags (int)
        Match: Optional Match class factory (defaults to lstring.re.Match)
    
    Returns:
        Pattern object (lstring.re.Pattern)
    """
    if Match is None:
        Match = globals()['Match']  # Use lstring.re.Match by default
    
    # Create Pattern using lstring.re.Pattern which will use the custom Match
    pattern_cls = globals()['Pattern']
    return pattern_cls(pattern, flags, Match=Match)


def match(pattern, string, flags=0):
    """
    Try to apply the pattern at the start of the string.
    
    Returns a Match object, or None if no match was found.
    """
    return _lstring.re.match(pattern, string, flags)


def search(pattern, string, flags=0):
    """
    Scan through string looking for a match to the pattern.
    
    Returns a Match object, or None if no match was found.
    """
    return _lstring.re.search(pattern, string, flags)


def fullmatch(pattern, string, flags=0):
    """
    Try to apply the pattern to the entire string.
    
    Returns a Match object, or None if no match was found.
    """
    return _lstring.re.fullmatch(pattern, string, flags)


def findall(pattern, string, flags=0):
    """
    Return a list of all non-overlapping matches in the string.
    """
    return _lstring.re.findall(pattern, string, flags)


def finditer(pattern, string, flags=0):
    """
    Return an iterator over all non-overlapping matches in the string.
    """
    return _lstring.re.finditer(pattern, string, flags)


def split(pattern, string, maxsplit=0, flags=0):
    """
    Split the source string by the occurrences of the pattern.
    """
    return _lstring.re.split(pattern, string, maxsplit, flags)


def sub(pattern, repl, string, count=0, flags=0):
    """
    Return the string obtained by replacing the leftmost
    non-overlapping occurrences of the pattern in string by the
    replacement repl.
    """
    return _lstring.re.sub(pattern, repl, string, count, flags)


def subn(pattern, repl, string, count=0, flags=0):
    """
    Return a 2-tuple containing (new_string, number).
    new_string is the string obtained by replacing the leftmost
    non-overlapping occurrences of the pattern in the source
    string by the replacement repl.  number is the number of
    substitutions that were made.
    """
    return _lstring.re.subn(pattern, repl, string, count, flags)


__all__ = [
    'Pattern',
    'Match',
    'compile',
    'match',
    'search',
    'fullmatch',
    'findall',
    'finditer',
    'split',
    'sub',
    'subn',
]
