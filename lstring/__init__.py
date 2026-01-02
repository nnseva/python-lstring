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


# Re-export utility functions from _lstring
get_optimize_threshold = _lstring.get_optimize_threshold
set_optimize_threshold = _lstring.set_optimize_threshold


__all__ = ['L', 'get_optimize_threshold', 'set_optimize_threshold']
