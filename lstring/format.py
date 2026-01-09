"""
Printf-style string formatting for lazy strings.

This module provides printf-style formatting (%) support for L instances,
allowing format strings to remain lazy while delegating actual formatting
to Python's built-in str % operator.
"""

import types
from typing import Union, Optional
from collections.abc import Mapping


def _printf_pos(format_str, placeholders: tuple):
    """
    Format a lazy string using positional printf-style placeholders.
    
    Args:
        format_str: Format string (L instance)
        placeholders: Tuple of values to substitute
    
    Returns:
        L: Formatted lazy string
    """
    from .lstring import L
    
    def format_parts():
        """Generator that yields formatted parts of the string."""
        last_pos = 0
        value_idx = 0
        length = len(format_str)
        
        while last_pos < length:
            # Find next %
            percent_pos = format_str.findc('%', last_pos)
            
            if percent_pos == -1:
                # No more placeholders - yield rest of string
                yield format_str[last_pos:]
                break
            
            # Yield static part before %
            if percent_pos > last_pos:
                yield format_str[last_pos:percent_pos]
            
            # Parse the placeholder
            end_pos, is_escape, star_count = format_str._parse_printf_positional(percent_pos)
            
            if end_pos == -1:
                # Invalid placeholder - let str % handle the error
                # Yield the % and continue
                yield L('%')
                last_pos = percent_pos + 1
                continue
            
            if is_escape:
                # %% escape sequence
                yield L('%')
                last_pos = end_pos
                continue
            
            # Valid placeholder - extract it
            placeholder = str(format_str[percent_pos:end_pos])
            
            # Extract values for this placeholder
            # We need star_count + 1 values: star_count for *, 1 for the actual value
            values = placeholders[value_idx:value_idx + star_count + 1]
            value_idx += star_count + 1
            
            # Format using str %
            formatted = placeholder % values
            yield L(formatted)
            
            last_pos = end_pos
    
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
    from .lstring import L
    
    # Convert all keys to L for consistent lookup
    # This handles both str and L keys in the input dict
    normalized_placeholders = {L(k) if isinstance(k, str) else k: v 
                               for k, v in placeholders.items()}
    
    def format_parts():
        """Generator that yields formatted parts of the string."""
        last_pos = 0
        length = len(format_str)
        
        while last_pos < length:
            # Find next %
            percent_pos = format_str.findc('%', last_pos)
            
            if percent_pos == -1:
                # No more placeholders - yield rest of string
                yield format_str[last_pos:]
                break
            
            # Yield static part before %
            if percent_pos > last_pos:
                yield format_str[last_pos:percent_pos]
            
            # Parse the placeholder
            end_pos, is_escape, name_end = format_str._parse_printf_named(percent_pos)
            
            if end_pos == -1:
                # Invalid or positional placeholder - let str % handle the error
                # Yield the % and continue
                yield L('%')
                last_pos = percent_pos + 1
                continue
            
            if is_escape:
                # %% escape sequence
                yield L('%')
                last_pos = end_pos
                continue
            
            # Valid named placeholder - extract it and the name
            placeholder = str(format_str[percent_pos:end_pos])
            name = format_str[percent_pos + 2:name_end - 1]  # Skip %( and )
            
            # Get value from dict
            value = normalized_placeholders[name]
            
            # Format using str %
            # Create a temporary dict with str key for formatting
            formatted = placeholder % {str(name): value}
            yield L(formatted)
            
            last_pos = end_pos
    
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
    from .lstring import L
    
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
    from .lstring import L
    
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
        
        # Parse placeholders using _parse_format_placeholder
        pos = 0
        length = len(format_str)
        
        while pos < length:
            # Find next { or }
            next_pos = format_str.findcs('{}', pos)
            
            if next_pos == -1:
                # No more braces - yield rest of string
                if last_pos < length:
                    yield format_str[last_pos:]
                break
            
            # Parse the token at this position
            end_pos, token_type, content_end = format_str._parse_format_placeholder(next_pos)
            
            if end_pos == -1:
                # Invalid/unclosed - skip this character
                pos = next_pos + 1
                continue
            
            # Yield static part before this token
            if next_pos > last_pos:
                yield format_str[last_pos:next_pos]
            
            if token_type == 1:
                # Literal {{ -> {
                yield L('{')
            elif token_type == 2:
                # Literal }} -> }
                yield L('}')
            elif token_type == 3:
                # Placeholder {content}
                content = format_str[next_pos + 1:content_end]
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
            
            last_pos = end_pos
            pos = end_pos
    
    return L('').join(format_parts())
