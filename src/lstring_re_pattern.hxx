#ifndef LSTRING_RE_PATTERN_HXX
#define LSTRING_RE_PATTERN_HXX

#include <Python.h>

// Forward declaration
template<typename CharT>
class LStrRegexBuffer;

// Temporary - will be redefined based on platform later
using CharT = Py_UCS4;

// Declaration of PatternObject
struct PatternObject {
    PyObject_HEAD
    LStrRegexBuffer<CharT> *buf;
    PyObject *match_factory; // Factory (class or callable) to create Match instances
};

// Register the Pattern type on the given submodule. Returns 0 on success,
// -1 on error (matching module exec convention).
int lstring_re_register_pattern_type(PyObject *submodule);

#endif // LSTRING_RE_PATTERN_HXX
