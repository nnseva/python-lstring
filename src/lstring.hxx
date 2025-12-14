/**
 * @file lstring.hxx
 * @brief Declarations for the lstr object and forward declarations.
 */

#ifndef LSTRING_HXX
#define LSTRING_HXX

#include <Python.h>

/** Forward declaration of Buffer to avoid cyclic include */
class Buffer;
/** Forward declare StrBuffer concrete type used by make_str_buffer */
class StrBuffer;

/**
 * @struct LStrObject
 * @brief C struct backing the Python `lstr` type.
 *
 * Instances of this struct are the low-level CPython object used to
 * implement the `_lstr` type. The `buffer` member points to a Buffer
 * implementation that lazily represents the string contents.
 */
struct LStrObject {
    PyObject_HEAD
    Buffer *buffer; /**< Pointer to the lazily-evaluated buffer */
};

/* Method table (defined in src/lstring_methods.cxx) */
extern PyMethodDef LStr_methods[];

/** Process-global optimize threshold declared in the module implementation. */
extern Py_ssize_t g_optimize_threshold;

#endif // LSTRING_HXX
