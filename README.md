[![CI](https://github.com/nnseva/python-lstring/actions/workflows/ci.yml/badge.svg)](https://github.com/nnseva/python-lstring/actions/workflows/ci.yml)

# True Python Lazy String

## Package Description

This package provides a true lazy string type for Python, designed to efficiently represent and manipulate Unicode strings without unnecessary copying or eager materialization. Unlike standard Python strings, which are always represented as separate contiguous memory regions, the lazy string type allows operations such as slicing, joining, formatting, and transformations to be composed and deferred until the result is actually needed. This approach can dramatically reduce memory usage and can sometimes improve performance in workloads involving large or complex string manipulations.

The core of the package is implemented as a C++ extension for maximum speed, with a clean Python interface. It is especially useful in scenarios where many intermediate string objects would otherwise be created, such as text processing pipelines, templating engines, or data transformation tasks. The package aims to be a drop-in enhancement for advanced users who need both the expressiveness of Python and the efficiency of lazy evaluation for string data.

## Installation

*Stable version* from the PyPi package repository
```bash
pip install python-lstring
```

*Last development version* from the GitHub source version control system
```
pip install git+git://github.com/nnseva/python-lstring.git
```

## Using

To use the lazy string type, simply import `L` from the `lstring` package:

```python
from lstring import L

# Create a lazy string from a regular Python string
s = L("Hello, world!")

# Lazy operations (no data copied yet)
s2 = s[7:] + "!" * 3  # slicing, multiplication, and concatenation are all lazy

# Materialize the result as a real Python string when needed
result = str(s2)
print(result)  # Output: world!!!!
```

You can chain multiple operations (slice, join, format, etc.) without creating intermediate strings. The actual computation and memory allocation happen only when you explicitly convert to a standard Python string (e.g., with `str()` or when passing to APIs that require a real string).

The lazy string type is compatible with Unicode and supports most common string operations.

## Internal Representation

Calling `repr()` on an instance of `L` returns a string that represents the instance’s internal structure: the stored operations used to build it (construction, slicing, multiplication, and addition of `L` instances).

A constructed instance of `L` is represented as a string prefixed with `L`.

Notice that `repr` call for `L` instance is not optimized and may be used only for debug purposes. 

```python
from lstring import L

print(repr((L('x') + L('y') + L('z') * 3)[1:2]))

# output:((L'x' + L'y') + L'z' * 3)[1:2]
```

## Specific L Operations

### Indexed Access

Rather the `str` type, `L` indexed access leads to return an `str` one-character instance:

```python
print(repr(L('qwerty')[3]))

# output: 'r'
```

### String Conversion

You may convert an `L` instance back to the `str` just applying `str` to it.

```python
print(repr(str((L('x') + L('y') + L('z') * 3)[1:3])))

# output: 'yz'
```

String formatting or printing also leads `L` to be converted back to the `str`:

```python
print((L('x') + L('y') + L('z') * 3)[1:3])

# output: yz
```

The original `L` instance stays unchanged.

## Lazy Operations

### Slicing

Applying slicing operation leads to construction of `L` instance referring the original `L` instance with slicing:

```python
print(repr(L('qwertyuiop')[2:4]))

# output: L'qwertyuiop'[2:4]
```

Stored slicing indexes may be adjusted depending on the actual length. The negative indexes are also adjusted to their slicing equivalents:

```python
print(repr(L('qwertyuiop')[-4:-2]))

# output: L'qwertyuiop'[6:8]

print(repr(L('qwertyuiop')[2:15]))

# output: L'qwertyuiop'[2:10]
```

Step differ from `1` is also supported:

```python
print(repr(L('qwertyuiop')[2:15:2]))

# output: L'qwertyuiop'[2:10:2]

print(repr(L('qwertyuiop')[15:2:-2]))

# output: L'qwertyuiop'[9:2:-2]
```
