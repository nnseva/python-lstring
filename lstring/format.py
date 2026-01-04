"""
Printf-style string formatting for lazy strings.

This module provides printf-style formatting (%) support for L instances,
allowing format strings to remain lazy while delegating actual formatting
to Python's built-in str % operator.
"""

from typing import Union
from collections.abc import Mapping


# Regex patterns will be initialized after module load to avoid circular imports
POSITIONAL_SPEC_PATTERN = None
NAMED_SPEC_PATTERN = None


def _init_patterns():
    """Initialize regex patterns for format specifiers."""
    global POSITIONAL_SPEC_PATTERN, NAMED_SPEC_PATTERN
    
    if POSITIONAL_SPEC_PATTERN is not None:
        return  # Already initialized
    
    from . import re
    
    # Regex pattern for positional (unnamed) printf-style format specifiers
    # Matches: %[flags][width][.precision][length]type
    # Named groups (boost::regex syntax):
    #   flags: #, 0, -, space, +
    #   width: number or *
    #   precision: number or * (without the dot)
    #   length: h, l, L (usually ignored in Python)
    #   type: d, i, o, u, x, X, e, E, f, F, g, G, c, r, s, a, %
    globals()['POSITIONAL_SPEC_PATTERN'] = re.compile(
        r'%(?<flags>[#0 +\-]*)(?<width>\*|\d+)?(?:\.(?<precision>\*|\d+))?(?<length>[hlL])?(?<type>[diouxXeEfFgGcrsa%])',
        compatible=False
    )
    
    # Regex pattern for named printf-style format specifiers
    # Matches: %(name)[flags][width][.precision][length]type OR %%
    # Named groups (boost::regex syntax):
    #   name: any characters except ) (only for named placeholders)
    #   flags, width, precision, length, type: same as positional (only for named placeholders)
    #   escape: % (only for %% escape sequences)
    # Note: Named placeholders don't support * wildcards (no "next value" concept in dicts)
    globals()['NAMED_SPEC_PATTERN'] = re.compile(
        r'%(?:\((?<name>[^)]+)\)(?<flags>[#0 +\-]*)(?<width>\d+)?(?:\.(?<precision>\d+))?(?<length>[hlL])?(?<type>[diouxXeEfFgGcrsa])|(?<escape>%))',
        compatible=False
    )
    
    POSITIONAL_SPEC_PATTERN = globals()['POSITIONAL_SPEC_PATTERN']
    NAMED_SPEC_PATTERN = globals()['NAMED_SPEC_PATTERN']


def _printf_pos(format_str, placeholders: tuple):
    """
    Format a lazy string using positional printf-style placeholders.
    
    Args:
        format_str: Format string (L instance)
        placeholders: Tuple of values to substitute
    
    Returns:
        L: Formatted lazy string
    """
    from . import L
    
    # Initialize patterns if needed
    _init_patterns()
    
    def format_parts():
        """Generator that yields formatted parts of the string."""
        last_pos = 0
        value_idx = 0
        
        for match in POSITIONAL_SPEC_PATTERN.finditer(format_str):
            # Yield static part before this match
            if match.start() > last_pos:
                yield format_str[last_pos:match.start()]
            
            # Get the matched specifier
            spec_type = match.group('type')
            
            # Handle %% escape sequence
            if spec_type == '%':
                yield L('%')
                last_pos = match.end()
                continue
            
            # Get the full placeholder text
            placeholder = str(match.group())
            
            # Count how many * wildcards are in the placeholder
            # Each * consumes an additional value from the tuple
            star_count = placeholder.count('*')
            
            # Extract values for this placeholder
            # If there are N stars, we need N+1 values: N for stars, 1 for the actual value
            values = placeholders[value_idx:value_idx + star_count + 1]
            value_idx += star_count + 1
            
            # Format the value using the original placeholder
            formatted = placeholder % values
            
            yield L(formatted)
            last_pos = match.end()
        
        # Yield remaining part after last match
        if last_pos < len(format_str):
            yield format_str[last_pos:]
    
    return L('').join(format_parts())


def _printf_dict(format_str, placeholders: Mapping):
    """
    Format a lazy string using named printf-style placeholders.
    
    Args:
        format_str: Format string (L instance)
        placeholders: Dict or Mapping of values to substitute
    
    Returns:
        L: Formatted lazy string
    """
    from . import L
    
    # Initialize patterns if needed
    _init_patterns()
    
    # Convert all keys to L for consistent lookup
    # This handles both str and L keys in the input dict
    normalized_placeholders = {L(k) if isinstance(k, str) else k: v 
                               for k, v in placeholders.items()}
    
    def format_parts():
        """Generator that yields formatted parts of the string."""
        last_pos = 0
        
        for match in NAMED_SPEC_PATTERN.finditer(format_str):
            # Yield static part before this match
            if match.start() > last_pos:
                yield format_str[last_pos:match.start()]
            
            # Check if this is an escape sequence
            if match.group('escape'):
                yield L('%')
            else:
                # Handle named placeholder
                # Get the full placeholder text and name
                placeholder = str(match.group())
                name = match.group('name')  # Returns L object
                
                # Get value from dict using the name
                value = normalized_placeholders[name]
                
                # Format the value using the original placeholder
                # Create a temporary dict with str key for formatting
                formatted = placeholder % {str(name): value}
                
                yield L(formatted)
            
            last_pos = match.end()
        
        # Yield remaining part after last match
        if last_pos < len(format_str):
            yield format_str[last_pos:]
    
    return L('').join(format_parts())


def printf(format_str, placeholders: Union[dict, tuple]):
    """
    Format a lazy string using printf-style formatting.
    
    This function implements printf-style (%) formatting for L instances.
    It finds format specifiers in the string, materializes only those parts,
    applies formatting using str's % operator, and joins the result.
    
    Args:
        format_str: Format string (L or str instance)
        placeholders: Values to substitute - either a dict for named placeholders
                     like %(name)s, or a tuple for positional placeholders like %s
    
    Returns:
        L: Formatted lazy string
    
    Examples:
        >>> printf(L('Hello %s'), ('world',))
        L('Hello world')
        >>> printf(L('%(name)s is %(age)d'), {'name': 'Alice', 'age': 30})
        L('Alice is 30')
        >>> printf(L('Pi: %.2f'), (3.14159,))
        L('Pi: 3.14')
    
    Notes:
        - Supports both positional (%s, %d, %f) and named (%(name)s) placeholders
        - Cannot mix positional and named placeholders in the same format string
        - Delegates actual formatting to Python's str % operator
        - Keeps non-formatted parts of the string lazy
    """
    # Import L here to avoid circular imports
    from . import L
    
    # Convert format_str to L if needed
    if isinstance(format_str, str):
        format_str = L(format_str)
    
    # Dispatch to appropriate function based on placeholders type
    if isinstance(placeholders, tuple):
        return _printf_pos(format_str, placeholders)
    elif isinstance(placeholders, Mapping):
        return _printf_dict(format_str, placeholders)
    else:
        # Single value - wrap in tuple for positional formatting
        return _printf_pos(format_str, (placeholders,))
