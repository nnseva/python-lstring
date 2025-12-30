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
    
    # Pre-created escape sequences for expand() method
    _ESCAPE_MAP = {
        '\\': L('\\'),
        'n': L('\n'),
        't': L('\t'),
        'r': L('\r'),
        'a': L('\a'),
        'b': L('\b'),
        'f': L('\f'),
        'v': L('\v'),
    }

    _ESCAPE_REGEX = None  # Placeholder for compiled regex to detect escapes

    @classmethod
    def _escape_regex(cls):
        """Compile regex to detect escape sequences in expand()."""
        if cls._ESCAPE_REGEX is None:
            cls._ESCAPE_REGEX = Pattern(
                r'^\\'
                r'(?:g<(?<named_or_num>[^>]+)>|'
                r'(?<octal_lead0>0[0-7]{0,2})|'
                r'(?<octal_3digit>[0-7]{3})|'
                r'(?<backref>[1-9][0-9]?)|'
                r'(?<escape>[ntrabfv\\])|'
                r'(?<invalid>.))'
            )
        return cls._ESCAPE_REGEX

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
            template_len = len(template)
            
            while i < template_len:
                # Find next backslash using efficient findc method
                backslash_pos = template.findc('\\', i)
                
                if backslash_pos == -1:
                    # No more backslashes, yield remainder and stop
                    if i < template_len:
                        yield template[i:]
                    break
                
                # Yield literal text before backslash
                if backslash_pos > i:
                    yield template[i:backslash_pos]
                # Process escape sequence
                m = self._escape_regex().match(template, backslash_pos)
                if not m:
                    raise ValueError(f"bad escape \\ at position {backslash_pos}")
                if m.group('invalid') is not None:
                    raise ValueError(f"bad escape \\{str(m.group('invalid'))} at position {backslash_pos}")
                if m.group('backref') is not None:
                    group_num = int(str(m.group('backref')))
                    group_value = self.group(group_num)
                    if group_value is not None:
                        yield group_value
                    else:
                        yield L('')
                elif m.group('named_or_num') is not None:
                    name = str(m.group('named_or_num'))
                    if name.isdigit():
                        group_num = int(name)
                        group_value = self.group(group_num)
                    else:
                        group_value = self.group(name)
                    if group_value is not None:
                        yield group_value
                    else:
                        yield L('')
                elif m.group('octal_lead0') is not None:
                    octal_str = str(m.group('octal_lead0'))
                    octal_value = int(octal_str, 8)
                    yield L(chr(octal_value))
                elif m.group('octal_3digit') is not None:
                    octal_str = str(m.group('octal_3digit'))
                    octal_value = int(octal_str, 8)
                    if octal_value > 0o377:
                        raise ValueError(f"octal escape value \\{octal_str} outside of range 0-0o377 at position {backslash_pos}")
                    yield L(chr(octal_value))
                elif m.group('escape') is not None:
                    c = str(m.group('escape'))
                    yield self._ESCAPE_MAP[c]
                else:
                    # should not reach here
                    raise ValueError(f"bad escape \\ at position {backslash_pos}")
                # Advance index past the matched escape sequence
                i = m.end()
        
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
    
    def sub(self, repl, string, count=0):
        """Return the string obtained by replacing occurrences of the pattern.
        
        Args:
            repl: Replacement string (str or L) or callable that takes Match object
            string: String to search in (str or L)
            count: Maximum number of replacements (0 = unlimited)
            
        Returns:
            lstring.L: String with replacements applied
        """
        if isinstance(string, str):
            string = L(string)
        
        # Use subn and discard the count
        return self.subn(repl, string, count)[0]
    
    def subn(self, repl, string, count=0):
        """Return a 2-tuple (new_string, number_of_substitutions).
        
        Args:
            repl: Replacement string (str or L) or callable that takes Match object
            string: String to search in (str or L)
            count: Maximum number of replacements (0 = unlimited)
            
        Returns:
            tuple: (lstring.L with replacements, number of substitutions made)
        """
        if isinstance(string, str):
            string = L(string)
        
        # Prepare replacement function
        if isinstance(repl, (str, type(L('')))):
            # String replacement: convert to L and use expand()
            if isinstance(repl, str):
                repl = L(repl)
            replacement_func = lambda m: m.expand(repl)
        else:
            # Callable replacement: use as is
            replacement_func = repl
        
        def generate_parts():
            """Generator that yields parts of the result string."""
            nonlocal n_subs
            pos = 0
            n_subs = 0
            
            while count == 0 or n_subs < count:
                m = self.search(string, pos)
                if m is None:
                    break
                
                # Yield literal text before match
                if m.start() > pos:
                    yield string[pos:m.start()]
                
                # Yield replacement
                yield replacement_func(m)
                
                # Move position forward
                new_pos = m.end()
                # Handle empty matches by advancing at least one position
                if new_pos == pos:
                    # Empty match - include the character at pos and advance
                    if pos < len(string):
                        yield string[pos:pos + 1]
                        pos += 1
                    else:
                        break
                else:
                    pos = new_pos
                
                n_subs += 1
            
            # Yield remaining text
            if pos < len(string):
                yield string[pos:]
        
        n_subs = 0
        result = L('').join(generate_parts())
        return (result, n_subs)


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
