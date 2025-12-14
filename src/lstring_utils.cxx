/**
 * @file lstring_utils.cxx
 * @brief Utility helpers for lstring: buffer creation and optimization helpers.
 */

#include <Python.h>
#include "lstring.hxx"
#include "lstring_utils.hxx"
#include "buffer.hxx"
#include "str_buffer.hxx"

/**
 * @brief Build a StrBuffer wrapper for a Python str.
 *
 * The returned StrBuffer takes ownership of any required state and wraps
 * the provided Python string. On error, nullptr is returned and a Python
 * exception is set.
 *
 * @param py_str Python str object (borrowed reference)
 * @return New StrBuffer* or nullptr on error.
 */
StrBuffer* make_str_buffer(PyObject *py_str) {
    switch (PyUnicode_KIND(py_str)) {
        case PyUnicode_1BYTE_KIND:
            return new Str8Buffer(py_str);
        case PyUnicode_2BYTE_KIND:
            return new Str16Buffer(py_str);
        case PyUnicode_4BYTE_KIND:
            return new Str32Buffer(py_str);
        default:
            PyErr_SetString(PyExc_RuntimeError, "Unsupported Unicode kind");
            return nullptr;
    }
}


/**
 * @brief Convert any non-StrBuffer into a concrete StrBuffer backed by a
 *        Python str.
 *
 * If the buffer already wraps a Python string, this is a no-op. On error
 * this function propagates the Python exception and leaves the object
 * unchanged.
 */
void lstr_collapse(LStrObject *self) {
    if (!self || !self->buffer) return;
    if (self->buffer->is_str()) return; // already a StrBuffer

    cppy::ptr py( PyObject_Str((PyObject*)self) );
    if (!py) {
        // propagate error to caller by leaving state unchanged
        return;
    }

    // Create new StrBuffer from the Python string
    StrBuffer *new_buf = make_str_buffer(py.get());
    if (!new_buf) {
        return; // make_str_buffer sets an error
    }

    // Replace buffer
    delete self->buffer;
    self->buffer = new_buf;
}


/**
 * @brief Try to collapse small lazy buffers into concrete StrBuffers.
 *
 * Uses the process-global `g_optimize_threshold` to decide whether to
 * collapse. If the threshold is inactive (<= 0), this is a no-op.
 */
void lstr_optimize(LStrObject *self) {
    if (!self || !self->buffer) return;
    if (self->buffer->is_str()) return;
    if (g_optimize_threshold <= 0) return;

    Py_ssize_t len = (Py_ssize_t)self->buffer->length();
    if (len < g_optimize_threshold) lstr_collapse(self);
}
