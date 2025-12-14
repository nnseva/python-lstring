/**
 * @file lstring.hxx
 * @brief Declarations for the lstr object and forward declarations.
 */

#ifndef LSTRING_HXX
#define LSTRING_HXX

#include <Python.h>

/** Forward declaration of Buffer to avoid cyclic include */
class Buffer;

/**
 * @struct LStrObject
 * @brief C struct backing the Python `lstr` type.
 *
 * Instances of this struct are the low-level CPython object used to
 * implement the `_lstr` type. The `buffer` member points to a Buffer
 * implementation that lazily represents the string contents.
 */
typedef struct {
    PyObject_HEAD
    Buffer *buffer; /**< Pointer to the lazily-evaluated buffer */
} LStrObject;

/**
 * @brief Collapse helper — convert any non-StrBuffer to a concrete StrBuffer.
 *
 * This function is defined in the implementation file and is exposed here
 * to allow other buffers to trigger explicit collapse operations on
 * `_lstr` instances.
 */
extern void lstr_collapse(LStrObject *self);

/* Forward declarations of lstr type methods. */
PyObject* LStr_new(PyTypeObject *type, PyObject *args, PyObject *kwds);
void LStr_dealloc(LStrObject *self);
Py_hash_t LStr_hash(LStrObject *self);
PyObject* LStr_repr(LStrObject *self);
PyObject* LStr_add(PyObject *left, PyObject *right);
PyObject* LStr_mul(PyObject *left, PyObject *right);
PyObject* LStr_str(LStrObject *self);
Py_ssize_t LStr_sq_length(PyObject *self);
PyObject* LStr_subscript(PyObject *self_obj, PyObject *key);
PyObject* LStr_richcompare(PyObject *a, PyObject *b, int op);
PyObject* LStr_collapse(LStrObject *self, PyObject *Py_UNUSED(ignored));
PyObject* LStr_find(LStrObject *self, PyObject *args, PyObject *kwds);
void lstr_optimize(LStrObject *self);

/**
 * @brief Module-local state structure used by the multi-phase init.
 *
 * Declared here so multiple implementation units can reference it
 * without defining it multiple times.
 */
typedef struct {
    PyObject *LStrType;
} lstring_state;

/**
 * @brief Retrieve the per-module state for the lstring module.
 *
 * Implemented in lstring_module.cxx.
 */
extern lstring_state* get_lstring_state(PyObject *module);

#endif // LSTRING_HXX
