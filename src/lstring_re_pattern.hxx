#ifndef LSTRING_RE_PATTERN_HXX
#define LSTRING_RE_PATTERN_HXX

#include <Python.h>

// Register the Pattern type on the given submodule. Returns 0 on success,
// -1 on error (matching module exec convention).
int lstring_re_register_pattern_type(PyObject *submodule);

#endif // LSTRING_RE_PATTERN_HXX
