#ifndef LSTRING_UTILS_HXX
#define LSTRING_UTILS_HXX

#include <Python.h>

class StrBuffer;
class LStrObject;

extern void lstr_collapse(LStrObject *self);
extern void lstr_optimize(LStrObject *self);
extern StrBuffer* make_str_buffer(PyObject *py_str);
extern PyObject* make_lstr_from_pystr(PyTypeObject *type, PyObject *py_str);

#endif // LSTRING_UTILS_HXX
