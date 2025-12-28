"""
lstring.re - Regular expression module for lazy strings

This module provides Python wrappers around the _lstring.re C extension,
exposing Pattern and Match classes that can be extended in Python.
"""

import _lstring


class Match(_lstring.re.Match):
    """
    Match object - a Python wrapper around the C++ implementation.
    
    Inherits from _lstring.re.Match to allow Python-level customization.
    """
    
    def __init__(self, pattern, subject):
        """
        Initialize a Match instance.
        
        Args:
            pattern: Pattern object
            subject: Subject string (str or lstring.L)
        """
        # Convert str to lstring.L if needed
        if isinstance(subject, str):
            subject = _lstring.L(subject)
        
        # Call C++ __init__
        _lstring.re.Match.__init__(self, pattern, subject)
    
    def group(self, *args):
        """Return one or more subgroups of the match."""
        # Convert str arguments to L
        converted_args = []
        for arg in args:
            if isinstance(arg, str):
                converted_args.append(_lstring.L(arg))
            else:
                converted_args.append(arg)
        return _lstring.re.Match.group(self, *converted_args)
    
    def __getitem__(self, key):
        """Return subgroup by index or name."""
        if isinstance(key, str):
            key = _lstring.L(key)
        return _lstring.re.Match.__getitem__(self, key)
    
    def start(self, group=0):
        """Return start position of group."""
        if isinstance(group, str):
            group = _lstring.L(group)
        return _lstring.re.Match.start(self, group)
    
    def end(self, group=0):
        """Return end position of group."""
        if isinstance(group, str):
            group = _lstring.L(group)
        return _lstring.re.Match.end(self, group)
    
    def span(self, group=0):
        """Return (start, end) tuple of group."""
        if isinstance(group, str):
            group = _lstring.L(group)
        return _lstring.re.Match.span(self, group)


class Pattern(_lstring.re.Pattern):
    """
    Compiled regular expression pattern - a Python wrapper around the C++ implementation.
    
    Inherits from _lstring.re.Pattern to allow Python-level customization while
    maintaining C++ performance for pattern matching operations.
    """
    
    def __init__(self, pattern, flags=0, Match=None):
        """
        Initialize a Pattern instance.
        
        Args:
            pattern: Pattern string (str or lstring.L)
            flags: Optional regex flags (int, defaults to 0)
            Match: Optional Match class factory (defaults to lstring.re.Match)
        """
        # Convert str to lstring.L if needed
        if isinstance(pattern, str):
            pattern = _lstring.L(pattern)
        
        if Match is None:
            Match = globals()['Match']  # Use lstring.re.Match by default
        
        # Call C++ __init__
        _lstring.re.Pattern.__init__(self, pattern, flags, Match)
    
    def match(self, string, pos=0, endpos=None):
        """Try to match pattern at the start of string."""
        if isinstance(string, str):
            string = _lstring.L(string)
        if endpos is None:
            return _lstring.re.Pattern.match(self, string, pos)
        return _lstring.re.Pattern.match(self, string, pos, endpos)
    
    def search(self, string, pos=0, endpos=None):
        """Scan through string looking for a match."""
        if isinstance(string, str):
            string = _lstring.L(string)
        if endpos is None:
            return _lstring.re.Pattern.search(self, string, pos)
        return _lstring.re.Pattern.search(self, string, pos, endpos)
    
    def fullmatch(self, string, pos=0, endpos=None):
        """Try to match the entire string."""
        if isinstance(string, str):
            string = _lstring.L(string)
        if endpos is None:
            return _lstring.re.Pattern.fullmatch(self, string, pos)
        return _lstring.re.Pattern.fullmatch(self, string, pos, endpos)
    
    def findall(self, string, pos=0, endpos=None):
        """Return a list of all non-overlapping matches.
        
        If one or more capturing groups are present in the pattern, return
        a list of groups; this will be a list of tuples if the pattern
        has more than one group.
        """
        if isinstance(string, str):
            string = _lstring.L(string)
        
        result = []
        for m in self.finditer(string, pos, endpos):
            groups = m.groups()
            if groups:
                # If pattern has capturing groups, return them
                if len(groups) == 1:
                    # Single group: return just the group value
                    result.append(groups[0])
                else:
                    # Multiple groups: return tuple of groups
                    result.append(groups)
            else:
                # No capturing groups: return full match
                result.append(m.group())
        
        return result
    
    def finditer(self, string, pos=0, endpos=None):
        """Return an iterator over all non-overlapping matches."""
        if isinstance(string, str):
            string = _lstring.L(string)
        
        # Use endpos as length if not specified
        if endpos is None:
            endpos = len(string)
        
        # Yield matches using search in a loop
        while pos <= endpos:
            m = _lstring.re.Pattern.search(self, string, pos, endpos)
            if m is None:
                break
            yield m
            
            # Move position forward
            new_pos = m.end()
            # Handle empty matches by advancing at least one position
            if new_pos == pos:
                pos += 1
            else:
                pos = new_pos
    
    def split(self, string, maxsplit=0):
        """Split string by occurrences of pattern.
        
        If capturing groups are in the pattern, their values are also
        included in the resulting list.
        """
        if isinstance(string, str):
            string = _lstring.L(string)
        
        result = []
        pos = 0
        splits = 0
        
        while maxsplit == 0 or splits < maxsplit:
            m = _lstring.re.Pattern.search(self, string, pos)
            if m is None:
                break
            
            # Add the part before the match
            result.append(string[pos:m.start()])
            
            # Add capturing groups if present
            groups = m.groups()
            if groups:
                result.extend(groups)
            
            # Move position forward
            new_pos = m.end()
            # Handle empty matches
            if new_pos == pos:
                if pos >= len(string):
                    break
                pos += 1
            else:
                pos = new_pos
            
            splits += 1
        
        # Add the remaining part
        result.append(string[pos:])
        
        return result


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
    pat = compile(pattern, flags)
    return pat.match(string)


def search(pattern, string, flags=0):
    """
    Scan through string looking for a match to the pattern.
    
    Returns a Match object, or None if no match was found.
    """
    pat = compile(pattern, flags)
    return pat.search(string)


def fullmatch(pattern, string, flags=0):
    """
    Try to apply the pattern to the entire string.
    
    Returns a Match object, or None if no match was found.
    """
    pat = compile(pattern, flags)
    return pat.fullmatch(string)


def findall(pattern, string, flags=0):
    """
    Return a list of all non-overlapping matches in the string.
    """
    pat = compile(pattern, flags)
    return pat.findall(string)


def finditer(pattern, string, flags=0):
    """
    Return an iterator over all non-overlapping matches in the string.
    """
    pat = compile(pattern, flags)
    return pat.finditer(string)


def split(pattern, string, maxsplit=0, flags=0):
    """
    Split the source string by the occurrences of the pattern.
    """
    pat = compile(pattern, flags)
    return pat.split(string, maxsplit)


def sub(pattern, repl, string, count=0, flags=0):
    """
    Return the string obtained by replacing the leftmost
    non-overlapping occurrences of the pattern in string by the
    replacement repl.
    """
    pat = compile(pattern, flags)
    return pat.sub(repl, string, count)


def subn(pattern, repl, string, count=0, flags=0):
    """
    Return a 2-tuple containing (new_string, number).
    new_string is the string obtained by replacing the leftmost
    non-overlapping occurrences of the pattern in the source
    string by the replacement repl.  number is the number of
    substitutions that were made.
    """
    pat = compile(pattern, flags)
    return pat.subn(repl, string, count)


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
