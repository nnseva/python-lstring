#ifndef LSTRING_UTILS_HXX
#define LSTRING_UTILS_HXX

#include <Python.h>

class StrBuffer;
class LStrObject;
class Buffer;

extern LStrObject *lstr_optimize(LStrObject *self);
extern StrBuffer* make_str_buffer(PyObject *py_str);
extern PyObject* make_lstr_from_pystr(PyTypeObject *type, PyObject *py_str);
// Return a new reference to the lstring.L type object by importing the
// '_lstring' module and reading its 'L' attribute. Caller owns the result.
extern PyObject* get_string_lstr_type();
// Create a new Python str from Buffer contents. Returns new reference or nullptr on error.
extern PyObject* buffer_to_pystr(const Buffer* buf);

#endif // LSTRING_UTILS_HXX
