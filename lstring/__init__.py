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


# Re-export utility functions from _lstring
get_optimize_threshold = _lstring.get_optimize_threshold
set_optimize_threshold = _lstring.set_optimize_threshold


__all__ = ['L', 'get_optimize_threshold', 'set_optimize_threshold']
