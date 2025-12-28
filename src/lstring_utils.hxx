#ifndef LSTRING_UTILS_HXX
#define LSTRING_UTILS_HXX

#include <Python.h>

class StrBuffer;
class LStrObject;

extern void lstr_collapse(LStrObject *self);
extern void lstr_optimize(LStrObject *self);
extern StrBuffer* make_str_buffer(PyObject *py_str);
extern PyObject* make_lstr_from_pystr(PyTypeObject *type, PyObject *py_str);
// Convenience overload: construct an lstring.L instance from a Python str
// by importing the module and using its L type.
extern PyObject* make_lstr_from_pystr(PyObject *py_str);
// Return a new reference to the lstring.L type object by importing the
// 'lstring' module and reading its 'L' attribute. Caller owns the result.
extern PyObject* get_string_lstr_type();

#endif // LSTRING_UTILS_HXX
