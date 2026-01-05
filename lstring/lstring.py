"""
lstring - Lazy string implementation for Python

This module provides a wrapper around the _lstring C extension,
exposing the L class and re submodule for lazy string operations.
"""

import _lstring
from enum import IntFlag
from functools import partial
from .format import printf, format as _format


class CharClass(IntFlag):
    """
    Character class flags for efficient character classification.
    
    These flags can be combined with bitwise OR to check multiple classes.
    """
    SPACE = _lstring.CHAR_SPACE
    ALPHA = _lstring.CHAR_ALPHA
    DIGIT = _lstring.CHAR_DIGIT
    ALNUM = _lstring.CHAR_ALNUM
    LOWER = _lstring.CHAR_LOWER
    UPPER = _lstring.CHAR_UPPER
    DECIMAL = _lstring.CHAR_DECIMAL
    NUMERIC = _lstring.CHAR_NUMERIC
    PRINTABLE = _lstring.CHAR_PRINTABLE


class L(_lstring.L):
    """
    Lazy string class - a Python wrapper around the C++ implementation.
    
    Inherits from _lstring.L to allow Python-level customization while
    maintaining C++ performance for core operations.
    """
    
    # ============================================================================
    # Comparison operators
    # ============================================================================
    
    def __eq__(self, other):
        """Compare for equality with str or L."""
        if isinstance(other, str):
            other = L(other)
        return super().__eq__(other)
    
    def __ne__(self, other):
        """Compare for inequality with str or L."""
        if isinstance(other, str):
            other = L(other)
        return super().__ne__(other)
    
    def __lt__(self, other):
        """Compare less than with str or L."""
        if isinstance(other, str):
            other = L(other)
        return super().__lt__(other)
    
    def __le__(self, other):
        """Compare less than or equal with str or L."""
        if isinstance(other, str):
            other = L(other)
        return super().__le__(other)
    
    def __gt__(self, other):
        """Compare greater than with str or L."""
        if isinstance(other, str):
            other = L(other)
        return super().__gt__(other)
    
    def __ge__(self, other):
        """Compare greater than or equal with str or L."""
        if isinstance(other, str):
            other = L(other)
        return super().__ge__(other)
    
    def __hash__(self):
        """Delegate hash to parent C++ implementation."""
        return super().__hash__()
    
    # ============================================================================
    # Formatting
    # ============================================================================
    
    def __mod__(self, values):
        """
        Printf-style string formatting using the % operator.
        
        Supports both positional and named placeholders:
        - Positional: %s, %d, %f, etc. with tuple or single value
        - Named: %(name)s, %(key)d, etc. with dict
        
        Args:
            values: Formatting values - tuple/single value for positional,
                   dict for named placeholders
        
        Returns:
            L: Formatted lazy string
        
        Examples:
            >>> L('Hello %s') % 'world'
            L('Hello world')
            >>> L('%(name)s is %(age)d') % {'name': 'Alice', 'age': 30}
            L('Alice is 30')
            >>> L('Value: %d') % 42
            L('Value: 42')
        """
        return printf(self, values)
    
    def format(self, *args, **kwargs):
        """
        Format string using str.format() syntax.
        
        Supports positional, numbered, and named placeholders:
        - Auto-numbered: {}, {:.2f}, {!r}
        - Numbered: {0}, {1}, {0:.2f}
        - Named: {name}, {key:.2f}, {obj.attr}
        
        Args:
            *args: Positional arguments for formatting
            **kwargs: Keyword arguments for formatting
        
        Returns:
            L: Formatted lazy string
        
        Examples:
            >>> L('Hello {}').format('world')
            L('Hello world')
            >>> L('{name} is {age}').format(name='Alice', age=30)
            L('Alice is 30')
            >>> L('{0} {1} {0}').format('hello', 'world')
            L('hello world hello')
        
        Notes:
            - Cannot mix auto-numbered ({}) and numbered ({0}) placeholders
            - Keeps non-formatted parts of the string lazy
            - Supports nested placeholders in format specs
        """
        return _format(self, args=args, kwargs=kwargs)
    
    def format_map(self, mapping):
        """
        Format string using a mapping, similar to str.format_map().
        
        Like format(**mapping), but uses the mapping directly without copying.
        This allows using dict subclasses with custom __missing__ methods.
        
        Args:
            mapping: A mapping object (typically a dict or dict subclass)
        
        Returns:
            L: Formatted lazy string
        
        Examples:
            >>> L('{name} is {age}').format_map({'name': 'Alice', 'age': 30})
            L('Alice is 30')
            >>> class Default(dict):
            ...     def __missing__(self, key):
            ...         return f'<{key}>'
            >>> L('{name} was born in {country}').format_map(Default(name='Guido'))
            L('Guido was born in <country>')
        
        Notes:
            - More efficient than format(**mapping) as it doesn't copy the dict
            - Allows custom dict subclasses with __missing__ to provide defaults
            - Cannot be used with positional arguments, only named placeholders
        """
        return _format(self, kwargs=mapping)
    
    # ============================================================================
    # Searching and Replacing
    # ============================================================================
    
    def startswith(self, prefix, start=None, end=None):
        """
        Check if string starts with the specified prefix.
        
        Args:
            prefix: String or L instance to check for
            start: Optional start position (default: 0)
            end: Optional end position (default: len(self))
        
        Returns:
            bool: True if string starts with prefix, False otherwise
        
        Examples:
            >>> L('hello world').startswith('hello')
            True
            >>> L('hello world').startswith('world')
            False
            >>> L('hello world').startswith('lo', 3)
            True
        """
        # Convert prefix to L if it's a string
        if isinstance(prefix, str):
            prefix = L(prefix)
        elif not isinstance(prefix, _lstring.L):
            raise TypeError(f"startswith first arg must be str or L, not {type(prefix).__name__}")
        
        # Handle start/end parameters
        length = len(self)
        if start is None:
            start = 0
        elif start < 0:
            start = max(0, length + start)
        
        if end is None:
            end = length
        elif end < 0:
            end = max(0, length + end)
        
        # Clamp to valid range
        start = max(0, min(start, length))
        end = max(start, min(end, length))
        
        # Get the substring to compare
        prefix_len = len(prefix)
        if prefix_len == 0:
            return True
        if prefix_len > (end - start):
            return False
        
        # Compare substring with prefix
        return self[start:start + prefix_len] == prefix
    
    def endswith(self, suffix, start=None, end=None):
        """
        Check if string ends with the specified suffix.
        
        Args:
            suffix: String or L instance to check for
            start: Optional start position (default: 0)
            end: Optional end position (default: len(self))
        
        Returns:
            bool: True if string ends with suffix, False otherwise
        
        Examples:
            >>> L('hello world').endswith('world')
            True
            >>> L('hello world').endswith('hello')
            False
            >>> L('hello world').endswith('lo', 0, 5)
            True
        """
        # Convert suffix to L if it's a string
        if isinstance(suffix, str):
            suffix = L(suffix)
        elif not isinstance(suffix, _lstring.L):
            raise TypeError(f"endswith first arg must be str or L, not {type(suffix).__name__}")
        
        # Handle start/end parameters
        length = len(self)
        if start is None:
            start = 0
        elif start < 0:
            start = max(0, length + start)
        
        if end is None:
            end = length
        elif end < 0:
            end = max(0, length + end)
        
        # Clamp to valid range
        start = max(0, min(start, length))
        end = max(start, min(end, length))
        
        # Get the substring to compare
        suffix_len = len(suffix)
        if suffix_len == 0:
            return True
        if suffix_len > (end - start):
            return False
        
        # Compare substring with suffix
        return self[end - suffix_len:end] == suffix
    
    def index(self, sub, start=None, end=None):
        """
        Find the lowest index where substring is found, raise ValueError if not found.
        
        Like find(), but raises ValueError when the substring is not found.
        
        Args:
            sub: Substring to search for (str or L instance)
            start: Optional start position (default: 0)
            end: Optional end position (default: len(self))
        
        Returns:
            int: Index of first occurrence of substring
        
        Raises:
            ValueError: If substring is not found
        
        Examples:
            >>> L('hello world').index('world')
            6
            >>> L('hello world').index('goodbye')
            Traceback (most recent call last):
                ...
            ValueError: substring not found
        """
        if start is None and end is None:
            result = self.find(sub)
        elif end is None:
            result = self.find(sub, start)
        else:
            result = self.find(sub, start, end)
        
        if result == -1:
            raise ValueError("substring not found")
        return result
    
    def rindex(self, sub, start=None, end=None):
        """
        Find the highest index where substring is found, raise ValueError if not found.
        
        Like rfind(), but raises ValueError when the substring is not found.
        
        Args:
            sub: Substring to search for (str or L instance)
            start: Optional start position (default: 0)
            end: Optional end position (default: len(self))
        
        Returns:
            int: Index of last occurrence of substring
        
        Raises:
            ValueError: If substring is not found
        
        Examples:
            >>> L('hello hello').rindex('hello')
            6
            >>> L('hello world').rindex('goodbye')
            Traceback (most recent call last):
                ...
            ValueError: substring not found
        """
        if start is None and end is None:
            result = self.rfind(sub)
        elif end is None:
            result = self.rfind(sub, start)
        else:
            result = self.rfind(sub, start, end)
        
        if result == -1:
            raise ValueError("substring not found")
        return result
    
    def count(self, sub, start=None, end=None):
        """
        Count non-overlapping occurrences of substring.
        
        Args:
            sub: Substring to count (str or L instance)
            start: Optional start position (default: 0)
            end: Optional end position (default: len(self))
        
        Returns:
            int: Number of non-overlapping occurrences
        
        Examples:
            >>> L('hello hello').count('hello')
            2
            >>> L('hello hello').count('l')
            4
            >>> L('aaaa').count('aa')
            2
        """
        # Convert sub to L if it's a string
        if isinstance(sub, str):
            sub = L(sub)
        elif not isinstance(sub, _lstring.L):
            raise TypeError(f"count first arg must be str or L, not {type(sub).__name__}")
        
        # Handle start/end parameters
        length = len(self)
        if start is None:
            start = 0
        elif start < 0:
            start = max(0, length + start)
        
        if end is None:
            end = length
        elif end < 0:
            end = max(0, length + end)
        
        # Clamp to valid range
        start = max(0, min(start, length))
        end = max(start, min(end, length))
        
        # Special case: empty substring
        sub_len = len(sub)
        if sub_len == 0:
            # Empty substring appears at every position including start and end
            return end - start + 1
        
        # Count non-overlapping occurrences using find
        count = 0
        pos = start
        while pos <= end - sub_len:
            found = self.find(sub, pos, end)
            if found == -1:
                break
            count += 1
            pos = found + sub_len
        
        return count
    
    def findcs(self, charset, start=None, end=None, invert=False):
        """
        Find first occurrence of any character from charset.
        
        Args:
            charset: Characters to search for (str, L instance, or any iterable)
            start: Optional start position (default: 0)
            end: Optional end position (default: len(self))
            invert: If True, find first character NOT in charset
        
        Returns:
            int: Index of first matching character, or -1 if not found
        
        Examples:
            >>> L('hello world').findcs('aeiou')
            1
            >>> L('hello world').findcs(['a', 'e', 'i'])
            1
            >>> L('hello world').findcs('xyz')
            -1
            >>> L('hello world').findcs('o', 0, 5)
            4
            >>> L('hello world').findcs('aeiou', invert=True)
            0
        """
        # Convert charset to L
        if isinstance(charset, str):
            charset = L(charset)
        elif not isinstance(charset, _lstring.L):
            # Try to treat as iterable and join into a string
            try:
                iter(charset)
                charset = L('').join(charset)
            except TypeError:
                # Not iterable, let C++ handle the error
                pass
        
        # Call the C++ implementation
        return super().findcs(charset, start, end, invert)
    
    def rfindcs(self, charset, start=None, end=None, invert=False):
        """
        Find last occurrence of any character from charset.
        
        Args:
            charset: Characters to search for (str, L instance, or any iterable)
            start: Optional start position (default: 0)
            end: Optional end position (default: len(self))
            invert: If True, find last character NOT in charset
        
        Returns:
            int: Index of last matching character, or -1 if not found
        
        Examples:
            >>> L('hello world').rfindcs('aeiou')
            7
            >>> L('hello world').rfindcs(['o', 'r', 'd'])
            10
            >>> L('hello world').rfindcs('xyz')
            -1
            >>> L('hello world').rfindcs('e', 0, 5)
            1
            >>> L('hello world').rfindcs('aeiou', invert=True)
            10
        """
        # Convert charset to L
        if isinstance(charset, str):
            charset = L(charset)
        elif not isinstance(charset, _lstring.L):
            # Try to treat as iterable and join into a string
            try:
                iter(charset)
                charset = L('').join(charset)
            except TypeError:
                # Not iterable, let C++ handle the error
                pass
        
        # Call the C++ implementation
        return super().rfindcs(charset, start, end, invert)
    
    def replace(self, old, new, count=-1):
        """
        Replace occurrences of substring old with new.
        
        Uses sequential find() to locate occurrences and constructs a generator
        of string segments that is passed to join().
        
        Args:
            old: Substring to replace (str or L instance)
            new: Replacement substring (str or L instance)
            count: Maximum number of replacements (default: -1 = all)
        
        Returns:
            L: New lazy string with replacements
        
        Examples:
            >>> L('hello world').replace('o', 'X')
            L('hellX wXrld')
            >>> L('hello hello').replace('hello', 'goodbye', 1)
            L('goodbye hello')
        """
        # Convert old and new to L instances
        if isinstance(old, str):
            old = L(old)
        elif not isinstance(old, _lstring.L):
            raise TypeError(f"replace() argument 1 must be str or L, not {type(old).__name__}")
        
        if isinstance(new, str):
            new = L(new)
        elif not isinstance(new, _lstring.L):
            raise TypeError(f"replace() argument 2 must be str or L, not {type(new).__name__}")
        
        # Special case: empty old substring
        old_len = len(old)
        if old_len == 0:
            raise ValueError("replace() cannot replace empty substring")
        
        # Generate segments, finding occurrences on the fly
        def segments():
            last_end = 0
            replacements_done = 0
            max_replacements = count if count >= 0 else float('inf')
            
            while replacements_done < max_replacements:
                found = self.find(old, last_end)
                if found == -1:
                    break
                
                # Yield segment before this occurrence plus replacement
                yield self[last_end:found] + new
                last_end = found + old_len
                replacements_done += 1
            
            # Yield final segment after last occurrence (if not empty)
            if last_end < len(self):
                yield self[last_end:]
        
        # Check if any replacements will be made
        first_occurrence = self.find(old, 0)
        if first_occurrence == -1:
            return self
        
        # Join segments without separator
        return L('').join(segments())
    
    # ============================================================================
    # Splitting and Joining
    # ============================================================================
    
    def split(self, sep=None, maxsplit=-1):
        """
        Split string by separator.
        
        Args:
            sep: Separator to split by (str or L instance, or None for whitespace)
            maxsplit: Maximum number of splits (default: -1 = all)
        
        Returns:
            list: List of L instances
        
        Examples:
            >>> L('a,b,c').split(',')
            [L('a'), L('b'), L('c')]
            >>> L('a  b  c').split()
            [L('a'), L('b'), L('c')]
            >>> L('a,b,c').split(',', 1)
            [L('a'), L('b,c')]
        """
        return list(self.split_iter(sep, maxsplit))
    
    def split_iter(self, sep=None, maxsplit=-1):
        """
        Split string by separator, returning an iterator.
        
        Args:
            sep: Separator to split by (str or L instance, or None for whitespace)
            maxsplit: Maximum number of splits (default: -1 = all)
        
        Yields:
            L instances
        
        Examples:
            >>> list(L('a,b,c').split_iter(','))
            [L('a'), L('b'), L('c')]
            >>> list(L('a  b  c').split_iter())
            [L('a'), L('b'), L('c')]
            >>> list(L('a,b,c').split_iter(',', 1))
            [L('a'), L('b,c')]
        """
        # Split by whitespace if sep is None
        if sep is None:
            yield from self._split_whitespace_iter(maxsplit)
            return
        
        # Convert sep to L if it's a string
        if isinstance(sep, str):
            sep = L(sep)
        elif not isinstance(sep, _lstring.L):
            raise TypeError(f"split() argument must be str or L, not {type(sep).__name__}")
        
        # Empty separator is not allowed
        sep_len = len(sep)
        if sep_len == 0:
            raise ValueError("empty separator")
        
        # Generate segments by splitting on separator
        last_end = 0
        splits_done = 0
        max_splits = maxsplit if maxsplit >= 0 else float('inf')
        
        while splits_done < max_splits:
            found = self.find(sep, last_end)
            if found == -1:
                break
            
            # Yield segment before separator (may be empty)
            yield self[last_end:found]
            last_end = found + sep_len
            splits_done += 1
        
        # Yield final segment
        yield self[last_end:]
    
    def _split_whitespace_iter(self, maxsplit=-1):
        """
        Split string by whitespace, merging consecutive whitespace, returning an iterator.
        
        Args:
            maxsplit: Maximum number of splits (default: -1 = all)
        
        Yields:
            L instances (non-empty)
        """
        length = len(self)
        pos = 0
        splits_done = 0
        max_splits = maxsplit if maxsplit >= 0 else float('inf')
        
        while pos < length and splits_done < max_splits:
            # Skip leading whitespace using findcc
            non_space = self.findcc(CharClass.SPACE, pos, length, invert=True)
            if non_space == -1:
                break
            pos = non_space
            
            if pos >= length:
                break
            
            # Find end of non-whitespace segment using findcc
            start = pos
            space = self.findcc(CharClass.SPACE, pos, length)
            if space == -1:
                pos = length
            else:
                pos = space
            
            # Yield segment
            yield self[start:pos]
            splits_done += 1
        
        # If we hit maxsplit, add the rest as final segment
        if splits_done >= max_splits and pos < length:
            # Skip leading whitespace of final segment using findcc
            non_space = self.findcc(CharClass.SPACE, pos, length, invert=True)
            if non_space != -1:
                yield self[non_space:]
    
    def rsplit(self, sep=None, maxsplit=-1):
        """
        Split string by separator from the right.
        
        Args:
            sep: Separator to split by (str or L instance, or None for whitespace)
            maxsplit: Maximum number of splits (default: -1 = all)
        
        Returns:
            list: List of L instances
        
        Examples:
            >>> L('a,b,c').rsplit(',')
            [L('a'), L('b'), L('c')]
            >>> L('a,b,c').rsplit(',', 1)
            [L('a,b'), L('c')]
        """
        # Reverse result since rsplit_iter yields from right to left
        return list(reversed(list(self.rsplit_iter(sep, maxsplit))))
    
    def rsplit_iter(self, sep=None, maxsplit=-1):
        """
        Split string by separator from the right, returning an iterator.
        
        Yields segments from right to left.
        
        Args:
            sep: Separator to split by (str or L instance, or None for whitespace)
            maxsplit: Maximum number of splits (default: -1 = all)
        
        Yields:
            L instances (from right to left)
        
        Examples:
            >>> list(reversed(list(L('a,b,c').rsplit_iter(','))))
            [L('a'), L('b'), L('c')]
            >>> list(reversed(list(L('a,b,c').rsplit_iter(',', 1))))
            [L('a,b'), L('c')]
        """
        # Split by whitespace if sep is None
        if sep is None:
            yield from self._rsplit_whitespace_iter(maxsplit)
            return
        
        # Convert sep to L if it's a string
        if isinstance(sep, str):
            sep = L(sep)
        elif not isinstance(sep, _lstring.L):
            raise TypeError(f"rsplit() argument must be str or L, not {type(sep).__name__}")
        
        # Empty separator is not allowed
        sep_len = len(sep)
        if sep_len == 0:
            raise ValueError("empty separator")
        
        # Generate segments by splitting on separator from right
        last_start = len(self)
        splits_done = 0
        max_splits = maxsplit if maxsplit >= 0 else float('inf')
        
        while splits_done < max_splits:
            found = self.rfind(sep, 0, last_start)
            if found == -1:
                break
            
            # Yield segment after separator (may be empty)
            yield self[found + sep_len:last_start]
            last_start = found
            splits_done += 1
        
        # Yield final segment (leftmost part)
        yield self[:last_start]
    
    def _rsplit_whitespace_iter(self, maxsplit=-1):
        """
        Split string by whitespace from the right, merging consecutive whitespace.
        
        Yields segments from right to left.
        
        Args:
            maxsplit: Maximum number of splits (default: -1 = all)
        
        Yields:
            L instances (non-empty, from right to left)
        """
        length = len(self)
        pos = length
        splits_done = 0
        max_splits = maxsplit if maxsplit >= 0 else float('inf')
        
        while pos > 0 and splits_done < max_splits:
            # Skip trailing whitespace using rfindcc
            non_space = self.rfindcc(CharClass.SPACE, 0, pos, invert=True)
            if non_space == -1:
                break
            pos = non_space + 1  # rfindcc returns index, we need position after it
            
            if pos <= 0:
                break
            
            # Find start of non-whitespace segment using rfindcc
            end = pos
            space = self.rfindcc(CharClass.SPACE, 0, pos)
            if space == -1:
                pos = 0
            else:
                pos = space + 1  # Position after the space
            
            # Yield segment
            yield self[pos:end]
            splits_done += 1
            
            # Move position to before the whitespace we just found
            if space != -1:
                pos = space
        
        # If we hit maxsplit, add the rest as final segment (everything remaining)
        if splits_done >= max_splits and pos > 0:
            # Find the last non-space character
            non_space = self.rfindcc(CharClass.SPACE, 0, pos, invert=True)
            if non_space != -1:
                yield self[:non_space + 1]
    
    def splitlines(self, keepends=False):
        """
        Split string by line boundaries.
        
        Line boundaries include: \\n, \\r, \\r\\n, \\v, \\f, \\x1c, \\x1d, \\x1e, \\x85, \\u2028, \\u2029
        
        Args:
            keepends: If True, line breaks are included in the resulting strings (default: False)
        
        Returns:
            list: List of L instances representing lines
        
        Examples:
            >>> L('hello\\nworld\\r\\ntest').splitlines()
            [L('hello'), L('world'), L('test')]
            >>> L('hello\\nworld\\n').splitlines(keepends=True)
            [L('hello\\n'), L('world\\n')]
            >>> L('line1\\r\\nline2').splitlines()
            [L('line1'), L('line2')]
        """
        return list(self.splitlines_iter(keepends))

    def splitlines_iter(self, keepends=False):
        """
        Split string by line boundaries, returning an iterator.
        
        Line boundaries include: \\n, \\r, \\r\\n, \\v, \\f, \\x1c, \\x1d, \\x1e, \\x85, \\u2028, \\u2029
        
        Args:
            keepends: If True, line breaks are included in the resulting strings (default: False)
        
        Yields:
            L instances representing lines
        
        Examples:
            >>> list(L('hello\\nworld\\r\\ntest').splitlines_iter())
            [L('hello'), L('world'), L('test')]
            >>> list(L('hello\\nworld\\n').splitlines_iter(keepends=True))
            [L('hello\\n'), L('world\\n')]
            >>> list(L('line1\\r\\nline2').splitlines_iter())
            [L('line1'), L('line2')]
        """
        # Line break characters according to Python's str.splitlines()
        # \n (LF), \r (CR), \v (VT), \f (FF), \x1c (FS), \x1d (GS), \x1e (RS)
        # \x85 (NEL), \u2028 (LS), \u2029 (PS)
        line_breaks = L('\n\r\v\f\x1c\x1d\x1e\x85\u2028\u2029')
        
        if len(self) == 0:
            return
        
        start = 0
        length = len(self)
        
        while start < length:
            # Find the next line break character using findcs
            pos = self.findcs(line_breaks, start)
            
            if pos == -1:
                # No more line breaks, add the rest
                if start < length:
                    yield self[start:]
                break
            
            # Check if it's \r\n (CRLF) - treat as single line break
            if pos < length - 1 and self[pos:pos+2] == L('\r\n'):
                # Found \r\n
                if keepends:
                    yield self[start:pos + 2]
                else:
                    yield self[start:pos]
                start = pos + 2
            else:
                # Single character line break
                if keepends:
                    yield self[start:pos + 1]
                else:
                    yield self[start:pos]
                start = pos + 1

    def partition(self, sep):
        """
        Partition string at first occurrence of separator.
        
        Returns a 3-tuple: (before, sep, after).
        If separator is not found, returns (str, L(''), L('')).
        
        Args:
            sep: Separator to partition by (str or L instance)
        
        Returns:
            tuple: (before, sep, after) as L instances
        
        Examples:
            >>> L('hello:world').partition(':')
            (L('hello'), L(':'), L('world'))
            >>> L('hello').partition(':')
            (L('hello'), L(''), L(''))
            >>> L('a:b:c').partition(':')
            (L('a'), L(':'), L('b:c'))
        """
        # Use split with maxsplit=1 (it will validate and convert sep)
        parts = self.split(sep, 1)
        
        if len(parts) == 1:
            # Separator not found
            return (self, L(''), L(''))
        else:
            # Separator found - convert sep to L if needed for return value
            if isinstance(sep, str):
                sep = L(sep)
            return (parts[0], sep, parts[1])
    
    def rpartition(self, sep):
        """
        Partition string at last occurrence of separator.
        
        Returns a 3-tuple: (before, sep, after).
        If separator is not found, returns (L(''), L(''), str).
        
        Args:
            sep: Separator to partition by (str or L instance)
        
        Returns:
            tuple: (before, sep, after) as L instances
        
        Examples:
            >>> L('hello:world').rpartition(':')
            (L('hello'), L(':'), L('world'))
            >>> L('hello').rpartition(':')
            (L(''), L(''), L('hello'))
            >>> L('a:b:c').rpartition(':')
            (L('a:b'), L(':'), L('c'))
        """
        # Use rsplit with maxsplit=1 (it will validate and convert sep)
        parts = self.rsplit(sep, 1)
        
        if len(parts) == 1:
            # Separator not found
            return (L(''), L(''), self)
        else:
            # Separator found - convert sep to L if needed for return value
            if isinstance(sep, str):
                sep = L(sep)
            return (parts[0], sep, parts[1])
    
    def join(self, iterable):
        """
        Join elements of iterable with self as separator.
        
        Uses recursive binary splitting to build a balanced tree structure
        for efficient lazy string operations.
        
        Args:
            iterable: An iterable of str or L instances
        
        Returns:
            L: A lazy string containing the joined elements
        
        Raises:
            TypeError: If any element is not str or L instance
        
        Examples:
            >>> L(', ').join(['a', 'b', 'c'])
            L('a, b, c')
            >>> L('').join(['hello', 'world'])
            L('helloworld')
        """
        # Convert iterable to list to allow indexing and length operations
        if isinstance(iterable, (list, tuple)):
            items = iterable
        else:
            items = list(iterable)
        
        # Convert all items to L instances, validating types
        converted_items = []
        for i, item in enumerate(items):
            if isinstance(item, _lstring.L):
                converted_items.append(item)
            elif isinstance(item, str):
                converted_items.append(L(item))
            else:
                raise TypeError(
                    f"sequence item {i}: expected str or L instance, "
                    f"{type(item).__name__} found"
                )
        
        # Special case: empty separator - just join without separator
        if len(self) == 0:
            return self._join_empty(converted_items)
        else:
            # Non-empty separator: append separator to all items except last
            if len(converted_items) == 0:
                return L('')
            elif len(converted_items) == 1:
                return converted_items[0]
            else:
                # Create new list where each item (except last) is concatenated with separator
                items_with_sep = [converted_items[i] + self for i in range(len(converted_items) - 1)] + [converted_items[-1]]
                return self._join_empty(items_with_sep)
    
    # ============================================================================
    # Case Manipulation
    # ============================================================================
    
    def lower(self):
        """
        Return a copy with all characters converted to lowercase.
        
        Returns:
            L: Lowercase version of the string
        
        Examples:
            >>> L('HELLO World').lower()
            L('hello world')
        """
        return L(str(self).lower())
    
    def upper(self):
        """
        Return a copy with all characters converted to uppercase.
        
        Returns:
            L: Uppercase version of the string
        
        Examples:
            >>> L('hello World').upper()
            L('HELLO WORLD')
        """
        return L(str(self).upper())
    
    def casefold(self):
        """
        Return a casefolded copy for caseless matching.
        
        Casefolding is similar to lowercasing but more aggressive,
        suitable for caseless string matching.
        
        Returns:
            L: Casefolded version of the string
        
        Examples:
            >>> L('ß').casefold()
            L('ss')
            >>> L('HELLO').casefold()
            L('hello')
        """
        return L(str(self).casefold())
    
    def capitalize(self):
        """
        Return a copy with first character capitalized and the rest lowercased.
        
        Returns:
            L: Capitalized version of the string
        
        Examples:
            >>> L('hello WORLD').capitalize()
            L('Hello world')
        """
        return L(str(self).capitalize())
    
    def title(self):
        """
        Return a titlecased version where words start with uppercase, rest lowercase.
        
        Returns:
            L: Titlecased version of the string
        
        Examples:
            >>> L('hello world').title()
            L('Hello World')
        """
        return L(str(self).title())
    
    def swapcase(self):
        """
        Return a copy with uppercase converted to lowercase and vice versa.
        
        Returns:
            L: String with swapped case
        
        Examples:
            >>> L('Hello World').swapcase()
            L('hELLO wORLD')
        """
        return L(str(self).swapcase())
    
    # ============================================================================
    # Padding and Stripping
    # ============================================================================
    
    def ljust(self, width, fillchar=' '):
        """
        Return left-justified string in a field of given width, padded with fillchar.
        
        Uses lazy multiplication to create padding.
        
        Args:
            width: Minimum width of resulting string
            fillchar: Character to use for padding (default: space)
        
        Returns:
            L: Left-justified string
        
        Examples:
            >>> L('hello').ljust(10)
            L('hello     ')
            >>> L('hello').ljust(10, '-')
            L('hello-----')
        """
        if not isinstance(fillchar, str) or len(fillchar) != 1:
            raise TypeError('fillchar must be a single character')
        
        current_len = len(self)
        if current_len >= width:
            return self
        
        padding_len = width - current_len
        padding = L(fillchar) * padding_len
        return self + padding
    
    def rjust(self, width, fillchar=' '):
        """
        Return right-justified string in a field of given width, padded with fillchar.
        
        Uses lazy multiplication to create padding.
        
        Args:
            width: Minimum width of resulting string
            fillchar: Character to use for padding (default: space)
        
        Returns:
            L: Right-justified string
        
        Examples:
            >>> L('hello').rjust(10)
            L('     hello')
            >>> L('hello').rjust(10, '-')
            L('-----hello')
        """
        if not isinstance(fillchar, str) or len(fillchar) != 1:
            raise TypeError('fillchar must be a single character')
        
        current_len = len(self)
        if current_len >= width:
            return self
        
        padding_len = width - current_len
        padding = L(fillchar) * padding_len
        return padding + self
    
    def center(self, width, fillchar=' '):
        """
        Return centered string in a field of given width, padded with fillchar.
        
        Uses lazy multiplication to create padding on both sides.
        
        Args:
            width: Minimum width of resulting string
            fillchar: Character to use for padding (default: space)
        
        Returns:
            L: Centered string
        
        Examples:
            >>> L('hello').center(11)
            L('   hello   ')
            >>> L('hello').center(10, '-')
            L('--hello---')
        """
        if not isinstance(fillchar, str) or len(fillchar) != 1:
            raise TypeError('fillchar must be a single character')
        
        current_len = len(self)
        if current_len >= width:
            return self
        
        total_padding = width - current_len
        left_padding_len = total_padding // 2
        right_padding_len = total_padding - left_padding_len
        
        left_padding = L(fillchar) * left_padding_len
        right_padding = L(fillchar) * right_padding_len
        return left_padding + self + right_padding
    
    def expandtabs(self, tabsize=8):
        """
        Return a copy with tabs expanded to spaces.
        
        Tabs are replaced with spaces to reach the next tab stop position.
        Tab stops occur at multiples of tabsize (default 8).
        Newlines reset the column position to 0.
        
        Args:
            tabsize: Number of spaces per tab stop (default: 8)
        
        Returns:
            L: String with tabs expanded to spaces
        
        Examples:
            >>> L('hello\\tworld').expandtabs()
            L('hello   world')  # Tab expands to 3 spaces (8 - 5)
            >>> L('a\\tb\\tc').expandtabs(4)
            L('a   b   c')  # Tabs expand to 3 spaces each
            >>> L('\\t\\t').expandtabs(4)
            L('        ')  # Each tab becomes 4 spaces
        """
        if tabsize <= 0:
            # When tabsize is 0 or negative, just remove tabs
            return self.replace(L('\t'), L(''))
        
        length = len(self)
        if length == 0:
            return self
        
        # Character set for search: tab and newline characters
        search_chars = L('\t\n\r')
        
        def generate_parts():
            """Generator that yields slices and space strings."""
            pos = 0
            column = 0
            
            while pos < length:
                # Find next tab or newline
                next_pos = self.findcs(search_chars, pos, length)
                
                if next_pos == -1:
                    # No more special chars, yield rest of string
                    if pos < length:
                        yield self[pos:]
                    break
                
                # Yield slice up to special char (if any)
                if next_pos > pos:
                    slice_part = self[pos:next_pos]
                    yield slice_part
                    column += next_pos - pos
                
                # Get the special character
                char = self[next_pos]
                
                if char == '\t':
                    # Calculate spaces needed to reach next tab stop
                    spaces_needed = tabsize - (column % tabsize)
                    yield L(' ') * spaces_needed
                    column += spaces_needed
                    pos = next_pos + 1
                elif char == '\n':
                    # Newline resets column
                    yield self[next_pos:next_pos + 1]
                    column = 0
                    pos = next_pos + 1
                elif char == '\r':
                    # Check for \r\n
                    if next_pos + 1 < length and self[next_pos + 1] == '\n':
                        # \r\n - yield both, reset column
                        yield self[next_pos:next_pos + 2]
                        column = 0
                        pos = next_pos + 2
                    else:
                        # Just \r - reset column
                        yield self[next_pos:next_pos + 1]
                        column = 0
                        pos = next_pos + 1
        
        return L('').join(generate_parts())
    
    def strip(self, chars=None):
        """
        Return a copy with leading and trailing characters removed.
        
        Uses lazy slicing to remove both leading and trailing whitespace or specified characters.
        Finds both boundaries and creates a single slice.
        
        Args:
            chars: String of characters to remove (default: whitespace)
        
        Returns:
            L: String with leading and trailing characters removed
        
        Examples:
            >>> L('  hello  ').strip()
            L('hello')
            >>> L('---hello---').strip('-')
            L('hello')
        """
        length = len(self)
        
        # Choose appropriate find functions using partial
        if chars is None:
            find_start = partial(self.findcc, CharClass.SPACE)
            find_end = partial(self.rfindcc, CharClass.SPACE)
        else:
            charset = L(chars) if isinstance(chars, str) else chars
            find_start = partial(self.findcs, charset)
            find_end = partial(self.rfindcs, charset)
        
        start = find_start(0, length, invert=True)
        if start == -1:  # All chars to strip
            return L('')
        end = find_end(0, length, invert=True)
        if start == 0 and end == length - 1:  # No chars to strip
            return self
        return self[start:end + 1]
    
    def lstrip(self, chars=None):
        """
        Return a copy with leading characters removed.
        
        Uses lazy slicing to remove leading whitespace or specified characters.
        Uses findcc for whitespace, findcs with invert for custom chars.
        
        Args:
            chars: String of characters to remove (default: whitespace)
        
        Returns:
            L: String with leading characters removed
        
        Examples:
            >>> L('  hello  ').lstrip()
            L('hello  ')
            >>> L('---hello---').lstrip('-')
            L('hello---')
        """
        length = len(self)
        
        # Choose appropriate find function using partial
        if chars is None:
            find_func = partial(self.findcc, CharClass.SPACE)
        else:
            find_func = partial(self.findcs, L(chars) if isinstance(chars, str) else chars)
        pos = find_func(0, length, invert=True)

        if pos == -1:  # All chars to strip
            return L('')
        if pos == 0:  # No leading chars to strip
            return self
        return self[pos:]
    
    def rstrip(self, chars=None):
        """
        Return a copy with trailing characters removed.
        
        Uses lazy slicing to remove trailing whitespace or specified characters.
        Uses rfindcc for whitespace, rfindcs with invert for custom chars.
        
        Args:
            chars: String of characters to remove (default: whitespace)
        
        Returns:
            L: String with trailing characters removed
        
        Examples:
            >>> L('  hello  ').rstrip()
            L('  hello')
            >>> L('---hello---').rstrip('-')
            L('---hello')
        """
        length = len(self)
        
        # Choose appropriate find function using partial
        if chars is None:
            find_func = partial(self.rfindcc, CharClass.SPACE)
        else:
            find_func = partial(self.rfindcs, L(chars) if isinstance(chars, str) else chars)
        pos = find_func(0, length, invert=True)

        if pos == -1:  # All chars to strip
            return L('')
        if pos == length - 1:  # No trailing chars to strip
            return self
        return self[:pos + 1]
    
    def zfill(self, width):
        """
        Pad string with zeros on the left to fill given width.
        
        If the string starts with a sign (+/-), zeros are inserted after the sign.
        Uses lazy slicing and rjust for padding.
        
        Args:
            width: Minimum width of resulting string
        
        Returns:
            L: Zero-padded string
        
        Examples:
            >>> L('42').zfill(5)
            L('00042')
            >>> L('-42').zfill(5)
            L('-0042')
            >>> L('+42').zfill(5)
            L('+0042')
        """
        length = len(self)
        
        # If already wide enough, return as is
        if length >= width:
            return self
        
        # Check for leading sign
        if length > 0:
            first_char = self[0]
            if first_char in ('+', '-'):
                # Sign present: insert zeros after sign
                return self[0:1] + self[1:].rjust(width - 1, '0')
        
        # No sign: just pad with zeros
        return self.rjust(width, '0')
    
    # ============================================================================
    # Translation and Encoding
    # ============================================================================
    
    def translate(self, table):
        """
        Return a copy with each character mapped through the translation table.
        
        Args:
            table: Translation table (mapping from Unicode ordinals to ordinals, strings, or None)
        
        Returns:
            L: Translated string
        
        Examples:
            >>> table = str.maketrans('aeiou', '12345')
            >>> L('hello world').translate(table)
            L('h2ll4 w4rld')
            >>> table = str.maketrans('', '', 'aeiou')
            >>> L('hello world').translate(table)
            L('hll wrld')
        """
        return L(str(self).translate(table))
    
    @staticmethod
    def maketrans(*args, **kwargs):
        """
        Create a translation table for use with translate().
        
        This is a static method that delegates to str.maketrans().
        
        Args:
            x: If only one argument, it must be a dictionary mapping ordinals to ordinals,
               strings, or None. If two or more arguments, this is a string of characters
               to be replaced.
            y: String of replacement characters (same length as x)
            z: String of characters to be deleted
        
        Returns:
            dict: Translation table
        
        Examples:
            >>> table = L.maketrans('aeiou', '12345')
            >>> L('hello').translate(table)
            L('h2ll4')
            >>> table = L.maketrans('', '', 'aeiou')
            >>> L('hello').translate(table)
            L('hll')
        """
        return str.maketrans(*args, **kwargs)
    
    def encode(self, encoding='utf-8', errors='strict'):
        """
        Encode string to bytes using the specified encoding.
        
        Args:
            encoding: The encoding to use (default: 'utf-8')
            errors: Error handling scheme (default: 'strict')
        
        Returns:
            bytes: Encoded byte string
        
        Examples:
            >>> L('hello').encode()
            b'hello'
            >>> L('привет').encode('utf-8')
            b'\\xd0\\xbf\\xd1\\x80\\xd0\\xb8\\xd0\\xb2\\xd0\\xb5\\xd1\\x82'
        """
        return str(self).encode(encoding, errors)
    
    # ============================================================================
    # Helper methods (private, used by other methods)
    # ============================================================================
    
    def _join_empty(self, items):
        """
        Helper method to join items without separator using recursive binary splitting.
        
        Builds a balanced tree by recursively dividing the list in half.
        
        Args:
            items: List of L instances to join
        
        Returns:
            L: Joined lazy string
        """
        if len(items) == 0:
            return L('')
        elif len(items) == 1:
            return items[0]
        elif len(items) == 2:
            return items[0] + items[1]
        else:
            # Divide list in half and recursively join each half
            mid = len(items) // 2
            left = self._join_empty(items[:mid])
            right = self._join_empty(items[mid:])
            return left + right


# Re-export utility functions from _lstring
get_optimize_threshold = _lstring.get_optimize_threshold
set_optimize_threshold = _lstring.set_optimize_threshold


__all__ = ['L', 'CharClass', 'get_optimize_threshold', 'set_optimize_threshold']
