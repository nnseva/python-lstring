"""
lstring.re - Regular expression module for lazy strings

This module provides Python wrappers around the _lstring.re C extension,
exposing Pattern and Match classes that can be extended in Python.
"""

import _lstring
from lstring import L
from enum import IntFlag

class RegexFlag(IntFlag):
    """Python `re`-like flags.

    Numeric values intentionally match CPython's `re` module.
    """

    IGNORECASE = 2
    MULTILINE = 8
    DOTALL = 16
    VERBOSE = 64

    I = IGNORECASE
    M = MULTILINE
    S = DOTALL
    X = VERBOSE


# Public flags (Python re-like).
#
# Note: Boost.Regex defaults differ from Python's `re` defaults for at least
# MULTILINE and DOTALL. We provide re-like flags here and translate them into
# Boost.Regex syntax flags when compiling patterns.
IGNORECASE = RegexFlag.IGNORECASE
I = RegexFlag.I
MULTILINE = RegexFlag.MULTILINE
M = RegexFlag.M
DOTALL = RegexFlag.DOTALL
S = RegexFlag.S
VERBOSE = RegexFlag.VERBOSE
X = RegexFlag.X

_PY_FLAG_MASK = IGNORECASE | MULTILINE | DOTALL | VERBOSE
# CPython's `re.UNICODE` flag bit. In modern Python it is the default for str
# patterns; we accept it for compatibility and ignore it silently.
_PY_UNICODE_FLAG = 32


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
                r'(?<invalid>.))',
                compatible=False
            )
        return cls._ESCAPE_REGEX

    def __init__(self, pattern, subject, pos=0, endpos=None):
        """
        Initialize a Match instance.
        
        Args:
            pattern: Pattern object
            subject: Subject string (str or lstring.L)
            pos: Start position used for matching
            endpos: End position used for matching (defaults to len(subject))
        """
        # Convert str to lstring.L if needed
        if isinstance(subject, str):
            subject = L(subject)
        if endpos is None:
            endpos = len(subject)
        # Call C++ __init__
        super().__init__(pattern, subject, pos, endpos)

    def _string_type(self):
        """Return the concrete runtime type of the underlying subject.

        Uses Match.string (C++ getter). Falls back to L if unavailable.
        """
        try:
            return type(self.string)
        except Exception:
            return L

    @property
    def lastgroup(self):
        """Name of the last matched capturing group, or None.

        Computed in Python using Match.lastindex (C++ getter) and the
        Pattern's cached named-group index.
        """
        lastindex = self.lastindex
        if lastindex is None:
            return None

        try:
            index = self.re.named_group_index
        except Exception:
            return None

        if lastindex < len(index):
            return index[lastindex]
        return None
    
    def group(self, *args):
        """Return one or more subgroups of the match."""
        # Convert str arguments to the runtime type of match subject.
        subject_type = self._string_type()
        converted_args = []
        for arg in args:
            if isinstance(arg, str):
                converted_args.append(subject_type(arg))
            else:
                converted_args.append(arg)
        return super().group(*converted_args)
    
    def __getitem__(self, key):
        """Return subgroup by index or name."""
        if isinstance(key, str):
            key = self._string_type()(key)
        return super().__getitem__(key)
    
    def start(self, group=0):
        """Return start position of group."""
        if isinstance(group, str):
            group = self._string_type()(group)
        return super().start(group)
    
    def end(self, group=0):
        """Return end position of group."""
        if isinstance(group, str):
            group = self._string_type()(group)
        return super().end(group)
    
    def span(self, group=0):
        """Return (start, end) tuple of group."""
        if isinstance(group, str):
            group = self._string_type()(group)
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

    @staticmethod
    def _to_boost_syntax_flags(flags: int) -> int:
        """Translate Python-like flags into Boost.Regex syntax flags.

        This function is used only in Python-compatible mode.

        Boost.Regex defaults differ from Python's `re` defaults (notably for
        MULTILINE and DOTALL), so we always apply Python defaults here by
        explicitly setting Boost's `no_mod_m` and `no_mod_s` unless the
        corresponding Python flag requests otherwise.

        Unsupported standard `re` flags are ignored with a warning, except
        UNICODE which is ignored silently.
        """
        import warnings

        flags_int = int(flags)

        # In compatible mode we expose a Python-like API, so we do not accept
        # arbitrary Boost-specific bits via `flags`. Warn and ignore anything
        # outside the supported Python-like subset, except UNICODE.
        supported = int(_PY_FLAG_MASK | _PY_UNICODE_FLAG)
        unsupported = flags_int & ~supported
        if unsupported:
            known = {
                1: 'TEMPLATE',
                4: 'LOCALE',
                128: 'DEBUG',
                256: 'ASCII',
            }
            parts = [name for bit, name in known.items() if unsupported & bit]
            remaining = unsupported & ~sum(known.keys())
            if remaining:
                parts.append(hex(remaining))
            details = '|'.join(parts) if parts else hex(unsupported)
            warnings.warn(
                f"Unsupported re flags in compatible mode are ignored: {details}",
                RuntimeWarning,
                stacklevel=3,
            )

        # Only supported Python-like bits remain (UNICODE ignored silently).
        flags_int &= int(_PY_FLAG_MASK)

        boost_flags = 0

        # If the extension doesn't expose Boost flag constants, fall back to
        # pass-through behaviour.
        try:
            boost_icase = int(_lstring.re.IGNORECASE)
            boost_no_mod_m = int(_lstring.re.NO_MOD_M)
            boost_no_mod_s = int(_lstring.re.NO_MOD_S)
            boost_mod_s = int(_lstring.re.MOD_S)
            boost_mod_x = int(_lstring.re.MOD_X)
        except Exception:
            return boost_flags

        # IGNORECASE
        if flags_int & IGNORECASE:
            boost_flags |= boost_icase

        # MULTILINE (Python default: off)
        if flags_int & MULTILINE:
            boost_flags &= ~boost_no_mod_m
        else:
            boost_flags |= boost_no_mod_m

        # DOTALL (Python default: off)
        if flags_int & DOTALL:
            boost_flags &= ~boost_no_mod_s
            boost_flags |= boost_mod_s
        else:
            boost_flags |= boost_no_mod_s
            boost_flags &= ~boost_mod_s

        # VERBOSE (Python default: off)
        if flags_int & VERBOSE:
            boost_flags |= boost_mod_x

        return boost_flags

    _INLINE_FLAG_FINDER_PATTERN = r"\(\?(?<flags>[aiLmsux-]+)(?<delim>[:)])"
    _INLINE_FLAG_FINDER = None

    # Note: In Boost.Regex, `\<` and `\>` are word-boundary tokens, not literal
    # angle brackets. We therefore keep `<`/`>` unescaped here.
    _NAMED_GROUP_FINDER_PATTERN = r"\(\?<(?![=!])(?<name>[A-Za-z_][A-Za-z0-9_]*)>"
    _NAMED_GROUP_FINDER = None

    @classmethod
    def _inline_flag_finder(cls):
        finder = cls._INLINE_FLAG_FINDER
        if finder is None:
            finder = cls(cls._INLINE_FLAG_FINDER_PATTERN, compatible=False)
            cls._INLINE_FLAG_FINDER = finder
        return finder

    @classmethod
    def _named_group_finder(cls):
        finder = cls._NAMED_GROUP_FINDER
        if finder is None:
            finder = cls(cls._NAMED_GROUP_FINDER_PATTERN, compatible=False)
            cls._NAMED_GROUP_FINDER = finder
        return finder

    @property
    def pattern(self):
        """The compiled pattern as an lstring.L.

        In Python-compatible mode this is the post-conversion pattern (Boost
        syntax) that was actually compiled.
        """
        return self._pattern

    @property
    def named_group_index(self):
        """Tuple mapping group index -> group name (or None).

        Lazily computed once and then cached on the Pattern instance.
        Index 0 corresponds to the whole match and is always None.
        """
        cached = getattr(self, '_named_group_index', None)
        if cached is not None:
            return cached

        # We intentionally keep this parser simple: it skips escaped chars and
        # character classes, and counts only plain capturing groups "(...)" and
        # named capturing groups "(?<name>...)".
        #
        # Important: named-group detection and name extraction is done via
        # Pattern's own regex finder (Boost-backed), not via manual substring
        # checks.
        finder = self._named_group_finder()

        index_to_name = [None]  # group 0
        group_count = 0

        escaped = False
        in_class = False
        i = 0
        n = len(self._pattern)
        while i < n:
            ch = self._pattern[i]

            if escaped:
                escaped = False
                i += 1
                continue

            if ch == '\\':
                escaped = True
                i += 1
                continue

            if ch == '[' and not in_class:
                in_class = True
                i += 1
                continue

            if ch == ']' and in_class:
                in_class = False
                i += 1
                continue

            if ch == '(' and not in_class:
                # Named capturing group: (?<name>...)
                m = finder.match(self._pattern, i)
                if m is not None:
                    group_count += 1
                    index_to_name.append(m.group('name'))
                else:
                    # Plain capturing group: (...)
                    next1 = self._pattern[i + 1] if i + 1 < n else ''
                    if next1 != '?':
                        group_count += 1
                        index_to_name.append(None)
                    # Otherwise treat "(?...)" as non-capturing (?:, ?=, ?!, ?<=, ?<!, etc.)

            i += 1

        cached = tuple(index_to_name)
        self._named_group_index = cached
        return cached
    
    @staticmethod
    def _convert_python_to_boost(pattern):
        r"""Convert Python re pattern syntax to Boost regex syntax.
        
        Converts:
        - (?P<name>...) to (?<name>...)  (named groups)
        - (?P=name) to \k<name>  (named backreferences)
        
        Args:
            pattern: Pattern string (lstring.L) with Python re syntax
            
        Returns:
            lstring.L: Pattern converted to Boost regex syntax
        """
        import warnings

        # Strip unsupported inline flags embedded in the pattern.
        # We search using Boost-backed regex (compatible=False), and keep
        # everything as L (no full conversion to str).
        #
        # Python supports inline flags like (?aiLmsux) and (?aiLmsux:...).
        # We ignore:
        #  - a: warn
        #  - L: warn
        #  - u: silently
        # while preserving other flags.
        def _strip_unsupported_inline_flags(pat: L) -> L:
            finder = Pattern._inline_flag_finder()

            def repl(m: Match) -> L:
                flags = m.group('flags')
                delim = m.group('delim')

                had_a = flags.findc('a', 0) != -1
                had_L = flags.findc('L', 0) != -1
                # 'u' is ignored silently (but removed)

                if had_a:
                    warnings.warn("Inline flag '(?a)' is ignored (ASCII mode is not supported).", RuntimeWarning, stacklevel=3)
                if had_L:
                    warnings.warn("Inline flag '(?L)' is ignored (locale mode is not supported).", RuntimeWarning, stacklevel=3)

                dash_pos = flags.findc('-', 0)
                if dash_pos != -1:
                    left = flags[:dash_pos]
                    right = flags[dash_pos + 1:]
                    right_nonempty = len(right) > 0
                else:
                    left = flags
                    right = L('')
                    right_nonempty = False

                def drop_unsupported(s: L) -> L:
                    kept = ''.join(c for c in s if c not in ('a', 'u', 'L'))
                    return L(kept)

                left2 = drop_unsupported(left)
                right2 = drop_unsupported(right)

                if right_nonempty:
                    if len(left2) and len(right2):
                        rebuilt = L('').join((left2, '-', right2))
                    elif len(left2) and not len(right2):
                        rebuilt = left2
                    elif not len(left2) and len(right2):
                        rebuilt = L('').join(('-', right2))
                    else:
                        rebuilt = L('')
                else:
                    rebuilt = left2

                if len(rebuilt) == 0:
                    # Only unsupported flags left.
                    if delim == ')':
                        return L('')
                    # Scoped flags group: (?a:...) -> (?:...)
                    return L('(?:')

                return L('').join(('(?', rebuilt, delim))

            return finder.sub(repl, pat)

        pattern = _strip_unsupported_inline_flags(pattern)

        def generate_parts():
            """Generator that yields parts of the converted pattern."""
            i = 0
            pattern_len = len(pattern)
            prefix = L('(?P')
            
            while i < pattern_len:
                # Find next occurrence of (?P
                pos = pattern.find(prefix, i)
                
                if pos == -1:
                    # No more Python syntax, yield remainder
                    if i < pattern_len:
                        yield pattern[i:]
                    break
                
                # Yield literal text before prefix
                if pos > i:
                    yield pattern[i:pos]
                
                # Check character after prefix
                if pos + 3 < pattern_len:
                    next_char = pattern[pos + 3]
                    if next_char == '<':
                        # (?P<name>...) -> (?<name>...)
                        # Just skip the 'P' character
                        yield pattern[pos:pos + 2]  # '(?'
                        i = pos + 3  # Skip '(?P'
                        continue
                    elif next_char == '=':
                        # (?P=name) -> \k<name>
                        # Find the closing )
                        j = pos + 4
                        while j < pattern_len and pattern[j] != ')':
                            j += 1
                        if j < pattern_len:
                            # Extract name
                            name = pattern[pos + 4:j]
                            yield L('\\k<')
                            yield name
                            yield L('>')
                            i = j + 1  # Skip past ')'
                            continue
                
                # Not a recognized pattern, copy prefix as-is
                yield pattern[pos:pos + 3]
                i = pos + 3
        
        return L('').join(generate_parts())
    
    def __init__(self, pattern, flags=0, Match=None, compatible=True):
        """
        Initialize a Pattern instance.
        
        Args:
            pattern: Pattern string (str or lstring.L)
            flags: Optional regex flags (int, defaults to 0)
            Match: Optional Match class factory (defaults to lstring.re.Match)
            compatible: If True, convert Python re syntax to Boost syntax (default: True)
        """
        # Convert str to lstring.L if needed
        if isinstance(pattern, str):
            pattern = L(pattern)
        
        if Match is None:
            Match = globals()['Match']  # Use lstring.re.Match by default
        
        # In Python-compatible mode, convert both pattern syntax and Python-like
        # flags (I/M/S/X) into the Boost.Regex equivalents.
        # In native/Boost mode, leave both pattern and flags untouched.
        if compatible:
            pattern = self._convert_python_to_boost(pattern)
            flags = self._to_boost_syntax_flags(flags)
        else:
            flags = int(flags)

        # Store the exact L pattern that will be compiled.
        self._pattern = pattern
        self._named_group_index = None
        
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
def compile(pattern, flags=0, Match=None, compatible=True):
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
    return Pattern(pattern, flags, Match=Match, compatible=compatible)


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
    'RegexFlag',
    'compile',
    'match',
    'search',
    'fullmatch',
    'findall',
    'finditer',
    'split',
    'sub',
    'subn',
    'IGNORECASE',
    'I',
    'MULTILINE',
    'M',
    'DOTALL',
    'S',
    'VERBOSE',
    'X',
]
