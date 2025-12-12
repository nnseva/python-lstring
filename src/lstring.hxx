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

#endif // LSTRING_HXX
