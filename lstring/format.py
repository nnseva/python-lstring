"""
Printf-style string formatting for lazy strings.

This module provides printf-style formatting (%) support for L instances,
allowing format strings to remain lazy while delegating actual formatting
to Python's built-in str % operator.
"""

import types
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


def _find_outer_placeholders(format_str):
    """
    Find all outer-level placeholders in a format string.
    
    Yields tuples of (start, end, content) for each placeholder,
    where content is the text inside {...} (without braces).
    Also yields ('literal', start, end) for literal {{ and }} sequences.
    
    Args:
        format_str: L instance containing format string
    
    Yields:
        tuple: ('placeholder', start, end, content) or ('literal', start, end, text)
    """
    pos = 0
    length = len(format_str)
    
    while pos < length:
        # Find next { or }
        open_pos = format_str.findc('{', pos)
        close_pos = format_str.findc('}', pos)
        
        # Determine which comes first
        if open_pos == -1 and close_pos == -1:
            break  # No more braces
        elif open_pos == -1:
            next_pos = close_pos
            next_char = '}'
        elif close_pos == -1:
            next_pos = open_pos
            next_char = '{'
        else:
            if open_pos < close_pos:
                next_pos = open_pos
                next_char = '{'
            else:
                next_pos = close_pos
                next_char = '}'
        
        # Check for escape sequences
        if next_char == '{':
            if next_pos + 1 < length and format_str[next_pos + 1] == '{':
                # {{ escape - literal {
                yield ('literal', next_pos, next_pos + 2, '{')
                pos = next_pos + 2
                continue
            else:
                # Start of placeholder - find matching }
                start = next_pos
                depth = 1
                pos = next_pos + 1
                
                while pos < length and depth > 0:
                    ch = format_str[pos]
                    if ch == '{':
                        depth += 1
                    elif ch == '}':
                        # Inside placeholder, } always closes a level
                        # No }} escape handling here - that's only at depth 0
                        depth -= 1
                    pos += 1
                
                if depth == 0:
                    # Found complete placeholder
                    content = format_str[start + 1:pos - 1]
                    yield ('placeholder', start, pos, content)
                else:
                    # Unclosed brace - let str.format handle the error
                    pos = start + 1
        else:  # next_char == '}'
            if next_pos + 1 < length and format_str[next_pos + 1] == '}':
                # }} escape - literal }
                yield ('literal', next_pos, next_pos + 2, '}')
                pos = next_pos + 2
            else:
                # Unmatched } - let str.format handle the error
                pos = next_pos + 1


def format(format_str, args=(), kwargs=types.MappingProxyType({})):
    """
    Format a lazy string using str.format() syntax.
    
    This function implements str.format() style formatting for L instances.
    It finds placeholders in the string, materializes only those parts,
    applies formatting using str's format() method, and joins the result.
    
    Args:
        format_str: Format string (L or str instance)
        args: Positional arguments for formatting (tuple or None)
        kwargs: Keyword arguments for formatting (dict or None)
    
    Returns:
        L: Formatted lazy string
    
    Examples:
        >>> format(L('Hello {}'), args=('world',))
        L('Hello world')
        >>> format(L('{name} is {age}'), kwargs={'name': 'Alice', 'age': 30})
        L('Alice is 30')
        >>> format(L('{0} {1} {0}'), args=('hello', 'world'))
        L('hello world hello')
    
    Notes:
        - Supports positional, numbered, and named placeholders
        - Cannot mix auto-numbered ({}) and numbered ({0}) placeholders
        - Keeps non-formatted parts of the string lazy
        - Format specs with nested placeholders are supported
    """
    from . import L
    
    # Convert format_str to L if needed
    if isinstance(format_str, str):
        format_str = L(format_str)
    
    # Create formatting function closure to avoid checking condition in loop
    # Use format_map when there are no positional args - works for both dict and Mapping
    if len(args) == 0:
        def do_format(placeholder_str, args_slice=()):
            return placeholder_str.format_map(kwargs)
    else:
        def do_format(placeholder_str, args_slice=args):
            return placeholder_str.format(*args_slice, **kwargs)
    
    def format_parts():
        """Generator that yields formatted parts of the string."""
        last_pos = 0
        auto_arg_index = 0  # For auto-numbered placeholders
        has_auto = False
        has_numbered = False
        
        for token in _find_outer_placeholders(format_str):
            token_type = token[0]
            start = token[1]
            end = token[2]
            
            # Yield static part before this token
            if start > last_pos:
                yield format_str[last_pos:start]
            
            if token_type == 'literal':
                # Literal { or } from escape sequence
                yield L(token[3])
            else:
                # Placeholder
                content = token[3]
                placeholder_str = '{' + str(content) + '}'
                
                # Determine placeholder type by looking at first character
                # Check if it's auto-numbered, numbered, or named
                if len(content) == 0 or content[0] in ':.![':
                    # Auto-numbered: {}, {:.2f}, {!r}
                    has_auto = True
                    if has_numbered:
                        raise ValueError("cannot mix auto and manual numbering")
                    
                    # Format with args[auto_arg_index:]
                    formatted = do_format(placeholder_str, args[auto_arg_index:])
                    auto_arg_index += 1
                    
                elif content[0].isdigit():
                    # Numbered: {0}, {1:.2f}
                    has_numbered = True
                    if has_auto:
                        raise ValueError("cannot mix auto and manual numbering")
                    
                    # Format with all args
                    formatted = do_format(placeholder_str)
                    
                else:
                    # Named or attribute/index access: {name}, {obj.attr}, {dict[key]}
                    # Format with all args and kwargs
                    formatted = do_format(placeholder_str)
                
                yield L(formatted)
            
            last_pos = end
        
        # Yield remaining part after last token
        if last_pos < len(format_str):
            yield format_str[last_pos:]
    
    return L('').join(format_parts())
