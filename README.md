[![CI](https://github.com/nnseva/python-lstring/actions/workflows/ci.yml/badge.svg)](https://github.com/nnseva/python-lstring/actions/workflows/ci.yml)

# True Python Lazy String

## AI/Agent-oriented documentation

If you are an AI agent (or using AI-assisted tooling) and want a repository map, invariants, and extension/optimization guidance, see [AI_CONTEXT.md](AI_CONTEXT.md).

## Package Description

This package provides a true lazy string type for Python, designed to efficiently represent and manipulate Unicode strings without unnecessary copying or eager materialization. Unlike standard Python strings, which are always represented as separate contiguous memory regions, the lazy string type allows operations such as slicing, joining, and formatting to be composed and deferred until the stringified result is actually needed. This approach can dramatically reduce memory usage and can sometimes improve performance in workloads involving large or complex string manipulations.

The core of the package is implemented as a C++ extension for maximum speed, with a clean Python interface. It is especially useful in scenarios where many intermediate string objects would otherwise be created, such as text processing pipelines, or templating engines. The package aims to be a drop-in enhancement for advanced users who need both the expressiveness of Python and the efficiency of lazy evaluation for string data.

## Installation

*Stable version* from the PyPI package index:
```bash
pip install lstring
```

*Latest development version* from GitHub:
```bash
pip install git+https://github.com/nnseva/python-lstring.git
```

## Usage

To use the lazy string type, import the `L` class from the `lstring` package and construct an `L` instance from any `str`. Most operations on `L` are lazy—they create new `L` objects that record the operation for later evaluation.

```python
from lstring import L

# Create a simple lazy string from a regular Python string
s = L("Hello, world!")

# Lazy operations (no data copied yet)
s2 = s[7:] + L("!") * 3  # slicing, multiplication, and concatenation are all lazy

# repr() shows the internal structure of the lazy string
print(repr(s2))
# output: (L'Hello, world!'[7:13] + (L'!' * 3))

# Materialize the result as a real Python string back when needed
result = str(s2)
print(repr(result))
# output: 'world!!!!'
```

You can chain multiple operations (slice, join, format, etc.) without creating intermediate strings. The actual computation and memory allocation happen only when you explicitly convert to a standard Python string (e.g., with `str()`), or when passing to APIs that require a real string.

The lazy string type is Unicode-aware and supports most common string operations.

Similar to `str`, `L` is *immutable* at the public API level: no operation changes an existing `L` instance in place (internal caches may be updated).

## Internal Representation

A *simple* `L` instance constructed directly from `str` is represented as a string prefixed with `L`:

```python
print(repr(L('qwerty')))

# output: L'qwerty'
```

The `L` instance keeps a reference to the `str` passed to the constructor.

A *compound* lazy `L` instance is constructed when any of the following operations is applied: `+` (concatenation), `*` (multiplication), or slicing (`[:]`).

**Note:** future versions of the package may extend the variety of compound lazy value kinds.

Calling `repr()` on any instance of `L` returns a string that represents the instance’s value’s internal structure.

**Note:** `repr(L(...))` is intended for debugging/testing. It is not optimized and the exact structure may change between versions.

```python
from lstring import L

print(repr((L('x') + L('y'))[0:1]))

# output: (L'x' + L'y')[0:1]
```

## Lazy Operations

### Slicing

Applying a slicing operation constructs a lazy `L` instance that refers to the original `L` instance with the given slice:

```python
print(repr(L('qwertyuiop')[2:4]))

# output: L'qwertyuiop'[2:4]
```

Stored slicing indices may be adjusted depending on the actual length. Negative indices are also adjusted to their slicing equivalents:

```python
print(repr(L('qwertyuiop')[-4:-2]))

# output: L'qwertyuiop'[6:8]

print(repr(L('qwertyuiop')[2:15]))

# output: L'qwertyuiop'[2:10]
```

A step other than `1` is also supported:

```python
print(repr(L('qwertyuiop')[2:15:2]))

# output: L'qwertyuiop'[2:10:2]

print(repr(L('qwertyuiop')[15:2:-2]))

# output: L'qwertyuiop'[9:2:-2]
```

### Multiplication

Applying multiplication constructs a new `L` instance that represents repeating the original value:

```python
print(repr(L('x') * 3))

# output: (L'x' * 3)
```

### Joining (concatenation)

Applying concatenation (`+`) constructs a new `L` instance that references the two operands:

```python
print(repr(L('x') + L('y')))

# output: (L'x' + L'y')
```

You can concatenate `L` with `str` in any order, an `L` instance for the `str` operand is created on demand:

```python
print(repr(L('x') + 'y'))

# output: (L'x' + L'y')
```

```python
print(repr('x' + L('y')))

# output: (L'x' + L'y')
```

Repeated concatenation with `+` automatically rebalances the concatenation tree (exact shape may vary):

```python
print(repr(L('1') + '2' + '3' + '4' + '5' + '6' + '7' + '8' + '9'))

# output: (((L'1' + L'2') + (L'3' + L'4')) + ((L'5' + L'6') + ((L'7' + L'8') + L'9')))
```

## Specific L Operations

### Construction from string

A *simple* `L` instance can be constructed from a string:

```python
print(repr(L('qwerty')))

# output: L'qwerty'
``` 

### Indexed Access

Unlike `str`, indexing an `L` returns a one-character `str` (not `L`):

```python
print(repr(L('qwerty')[3]))

# output: 'r'
```

### String Conversion

You may convert an `L` instance back to `str` by applying `str()` to it.

```python
print(repr(str((L('x') + L('y') + L('z') * 3)[1:3])))

# output: 'yz'
```

String formatting or printing also leads `L` to be converted back to the `str`:

```python
print((L('x') + L('y') + L('z') * 3)[1:3])

# output: yz
```

**Note:** a simple `L` instance constructed from `str` returns the original `str` object from `str(L(...))` (no copy).

### Small-result materialization

`lstring.set_optimize_threshold(threshold: int)` sets a length threshold: results shorter than the threshold will be materialized into a simple `L` (backed by a `str`), rather than remaining as a compound lazy value:

```python
lstring.set_optimize_threshold(10)
print(repr((L('x') + L('y') + L('z') * 3)[1:3]))

# output: L'yz'
```

`lstring.set_optimize_threshold()` is process-global and affects all `L` operations.

The `lstring.get_optimize_threshold()` function returns the current threshold value.

## Formatting methods and operators

### The `format` and `format_map` methods

`L.format` and `L.format_map` behave similarly to `str.format` and `str.format_map`, respectively.

Actually, the implementation splits the format string to static and dynamic parts, and concatenates static parts with values converted by the `str.format` function calls. The result is a compound `L` value.

```python
print(repr('value: {}'.format(1)))
# output: 'value: 1'

print(repr(L('value: {}').format(1)))
# output: (L'value: {}'[0:7] + L'1')

print(repr(str(L('value: {}').format(1))))
# output: 'value: 1'
```

### `%`-style (`printf`-like) formatting

The `%` operator behaves similarly to the `%` operator of the `str`.

Actually, the implementation splits the format string to static and dynamic parts, and concatenates static parts with values converted by the `%` operation of the `str`. The result is a compound `L` value.

```python
print(repr('value: %s' % 1))
# output: 'value: 1'

print(repr(L('value: %s') % 1))
# output: (L'value: %s'[0:7] + L'1')

print(repr(str(L('value: %s') % 1)))
# output: 'value: 1'
```

### `f`-string-like formatting

An `f`-string is Python-specific syntax sugar that allows using the `f` prefix on a string literal to embed runtime values and format them.

`L` supports similar behavior via the `L.f()` method. Almost any Python expression is allowed, similar to standard `f`-strings.

You may pass `globals()` and `locals()` explicitly to `L.f()`. By default it uses the caller's `globals()` and `locals()`.

Actually, the implementation splits the format string to static and dynamic parts, and concatenates static parts with values converted by the `format` method of the `str`. The result is a compound `L` value.

```python
print(repr(f'value: {1}'))
# output: 'value: 1'

print(repr(L('value: {1}').f()))
# output: (L'value: {1}'[0:7] + L'1')

print(repr(str(L('value: {1}').f())))
# output: 'value: 1'
```

## Standard string operations

Most commonly documented `str` operations are supported:

- formatting
    - `L.format` and `L.format_map` (see above)
    - `f`-string formatting (`L.f()` method see above)
    - `%` (`printf`-like) formatting (see above)
    - `L.zfill`
- Searching and replacing
    - `L.find`, `L.rfind`
    - `L.index`, `L.rindex`
    - `L.startswith`, `L.endswith`
    - `L.count`
    - `L.replace`
- Splitting and joining
    - `L.split`, `L.rsplit`
    - `L.splitlines`
    - `L.partition`, `L.rpartition`
    - `L.join`
- Classification
    - `L.isalpha`
    - `L.isdecimal`
    - `L.isdigit`
    - `L.isnumeric`
    - `L.isalnum`
    - `L.isidentifier`
    - `L.islower`
    - `L.isupper`
    - `L.istitle`
    - `L.isspace`
    - `L.isprintable`
- Case manipulation
    - `L.lower`
    - `L.upper`
    - `L.casefold`
    - `L.capitalize`
    - `L.title`
    - `L.swapcase`
- Translation and Encoding
    - `L.translate`
    - `L.maketrans`
    - `L.encode`

**Note:** for maximum compatibility, some methods are implemented by converting to `str` and delegating to CPython:

- All case manipulation operations
    - `L.lower`
    - `L.upper`
    - `L.casefold`
    - `L.capitalize`
    - `L.title`
    - `L.swapcase`
- Some classification operations
    - `L.isidentifier`
- All translation and encoding
    - `L.translate`
    - `L.maketrans`
    - `L.encode`

Implementation of these methods may be improved in the future package versions to avoid conversion to `str` instance.

## Non-standard searching methods

Several additional searching methods are provided on `L`. They use implementation-specific details to search characters efficiently.

They search for the position of a single character or any character from a character set, and return `-1` if not found.

The `start` and `end` parameters define the search slice `[start, end)`.

The `r`-prefixed methods search the position from the right.

### Find a single character

```python
L.findc(ch, start=None, end=None)
L.rfindc(ch, start=None, end=None)
```

Find a single character code point `ch`.

The character may be represented as a single-char string, or a codepoint integer value.

### Find a character set

```python
L.findcs(cs, start=None, end=None, invert=False)
L.rfindcs(cs, start=None, end=None, invert=False)
```

Find any character code point from the character set `cs`.

The character set may be represented as `str` or `L` value.

The `invert` parameter may be used to invert the character set.

### Find a character range

```python
L.findcr(startcp, endcp, start=None, end=None, invert=False)
L.rfindcr(startcp, endcp, start=None, end=None, invert=False)
```

Find any character code point from the character range `[startcp, endcp)`.

Both `startcp` and `endcp` may be represented as integer values, or single-character `str` instances.

The `invert` parameter may be used to invert the searching character set to exclude the character range from the full Unicode character range instead.

### Find a character class

```python
L.findcc(class_mask, start=None, end=None, invert=False)
L.rfindcc(class_mask, start=None, end=None, invert=False)
```

Find any character code point related to the character classes of the `class_mask`.

The `class_mask` may be combined from the `lstring.CharClass` enum values using bitwise OR, like:

```python
class_mask = CharClass.LOWER | CharClass.DIGIT
```

The `invert` parameter may be used to invert the searching character class mask.
