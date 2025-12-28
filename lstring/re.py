"""
lstring.re - Regular expression module for lazy strings

This module provides Python wrappers around the _lstring.re C extension,
exposing Pattern and Match classes that can be extended in Python.
"""

import _lstring
from lstring import L


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
            subject = L(subject)
        
        # Call C++ __init__
        super().__init__(pattern, subject)
    
    def group(self, *args):
        """Return one or more subgroups of the match."""
        # Convert str arguments to L
        converted_args = []
        for arg in args:
            if isinstance(arg, str):
                converted_args.append(L(arg))
            else:
                converted_args.append(arg)
        return super().group(*converted_args)
    
    def __getitem__(self, key):
        """Return subgroup by index or name."""
        if isinstance(key, str):
            key = L(key)
        return super().__getitem__(key)
    
    def start(self, group=0):
        """Return start position of group."""
        if isinstance(group, str):
            group = L(group)
        return super().start(group)
    
    def end(self, group=0):
        """Return end position of group."""
        if isinstance(group, str):
            group = L(group)
        return super().end(group)
    
    def span(self, group=0):
        """Return (start, end) tuple of group."""
        if isinstance(group, str):
            group = L(group)
        return super().span(group)
    
    def expand(self, template):
        """Return the string obtained by doing backslash substitution on template.
        
        Escape sequences such as \\n are converted to appropriate characters,
        and numeric backreferences (\\1, \\2) and named backreferences (\\g<name>)
        are replaced by the corresponding group.
        
        Args:
            template: Template string (str or lstring.L) with backreferences
            
        Returns:
            lstring.L: Expanded string with all substitutions applied
        """
        # Convert str template to L for uniform handling
        if isinstance(template, str):
            template = L(template)
        
        def generate_parts():
            """Generator that yields parts of the expanded template."""
            nonlocal template
            i = 0
            last_pos = 0
            template_len = len(template)
            
            while i < template_len:
                if str(template[i]) == '\\':
                    # Yield text before escape sequence
                    if i > last_pos:
                        yield template[last_pos:i]
                    
                    i += 1
                    
                    if i >= template_len:
                        raise ValueError(f"bad escape \\ at position {i-1}")
                    
                    c = str(template[i])
                    
                    # Numeric backreference \1, \2, ..., \99
                    if c.isdigit():
                        group_num = int(c)
                        # Check for two-digit group number
                        if i + 1 < template_len and str(template[i + 1]).isdigit():
                            group_num = group_num * 10 + int(str(template[i + 1]))
                            i += 1
                        
                        # Get group content (or empty string if not matched)
                        group_value = self.group(group_num)
                        if group_value is not None:
                            yield group_value
                        else:
                            yield L('')
                    
                    # Named/numbered group \g<name> or \g<0>
                    elif c == 'g' and i + 1 < template_len and str(template[i + 1]) == '<':
                        i += 2  # skip 'g<'
                        start = i
                        
                        # Find closing '>'
                        while i < template_len and str(template[i]) != '>':
                            i += 1
                        
                        if i >= template_len:
                            raise ValueError(f"missing >, unterminated name at position {start - 2}")
                        
                        name = template[start:i]
                        name_str = str(name)
                        
                        # Check if name is a number
                        if name_str.isdigit():
                            group_num = int(name_str)
                            group_value = self.group(group_num)
                        else:
                            # Named group
                            group_value = self.group(name_str)
                        
                        if group_value is not None:
                            yield group_value
                        else:
                            yield L('')
                    
                    # Escaped backslash
                    elif c == '\\':
                        yield L('\\')
                    
                    # Escape sequences
                    elif c == 'n':
                        yield L('\n')
                    elif c == 't':
                        yield L('\t')
                    elif c == 'r':
                        yield L('\r')
                    elif c == 'a':
                        yield L('\a')
                    elif c == 'b':
                        yield L('\b')
                    elif c == 'f':
                        yield L('\f')
                    elif c == 'v':
                        yield L('\v')
                    
                    else:
                        raise ValueError(f"bad escape \\{c} at position {i-1}")
                    
                    i += 1
                    last_pos = i
                else:
                    i += 1
            
            # Yield remainder of template
            if last_pos < template_len:
                yield template[last_pos:]
        
        # Use join to build balanced tree from generated parts
        return L('').join(generate_parts())


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
            pattern = L(pattern)
        
        if Match is None:
            Match = globals()['Match']  # Use lstring.re.Match by default
        
        # Call C++ __init__
        super().__init__(pattern, flags, Match)
    
    def match(self, string, pos=0, endpos=None):
        """Try to match pattern at the start of string."""
        if isinstance(string, str):
            string = L(string)
        if endpos is None:
            return super().match(string, pos)
        return super().match(string, pos, endpos)
    
    def search(self, string, pos=0, endpos=None):
        """Scan through string looking for a match."""
        if isinstance(string, str):
            string = L(string)
        if endpos is None:
            return super().search(string, pos)
        return super().search(string, pos, endpos)
    
    def fullmatch(self, string, pos=0, endpos=None):
        """Try to match the entire string."""
        if isinstance(string, str):
            string = L(string)
        if endpos is None:
            return super().fullmatch(string, pos)
        return super().fullmatch(string, pos, endpos)
    
    def findall(self, string, pos=0, endpos=None):
        """Return a list of all non-overlapping matches.
        
        If one or more capturing groups are present in the pattern, return
        a list of groups; this will be a list of tuples if the pattern
        has more than one group.
        """
        if isinstance(string, str):
            string = L(string)
        
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
            string = L(string)
        
        # Use endpos as length if not specified
        if endpos is None:
            endpos = len(string)
        
        # Yield matches using search in a loop
        while pos <= endpos:
            m = super().search(string, pos, endpos)
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
            string = L(string)
        
        result = []
        pos = 0
        splits = 0
        
        while maxsplit == 0 or splits < maxsplit:
            m = super().search(string, pos)
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
