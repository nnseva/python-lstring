/**
 * @file lstring_utils.cxx
 * @brief Utility helpers for lstring: buffer creation and optimization helpers.
 */

#include <Python.h>
#include "lstring.hxx"
#include "lstring_utils.hxx"
#include <cppy/cppy.h>
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


/**
 * @brief Create a new L instance (heap type `type`) that wraps the
 *        provided Python string `py_str`.
 *
 * The function allocates the object via tp_alloc, builds a StrBuffer for
 * the given Python string, and returns an owned reference to the new
 * object. On error, nullptr is returned and a Python exception is set.
 */
PyObject* make_lstr_from_pystr(PyTypeObject *type, PyObject *py_str) {
    if (!PyUnicode_Check(py_str)) {
        PyErr_SetString(PyExc_TypeError, "py_str must be a str");
        return nullptr;
    }

    LStrObject *self = (LStrObject*)type->tp_alloc(type, 0);
    if (!self) return nullptr;
    cppy::ptr self_owner((PyObject*)self);

    try {
        self->buffer = make_str_buffer(py_str);
        if (!self->buffer) return nullptr; // make_str_buffer sets PyErr
    } catch (const std::exception &e) {
        PyErr_SetString(PyExc_RuntimeError, e.what());
        return nullptr;
    } catch (...) {
        PyErr_SetString(PyExc_RuntimeError, "Buffer allocation failed");
        return nullptr;
    }

    return self_owner.release();
}

// Convenience overload: take a Python str and construct an lstring.L instance
// by importing the module and using its `L` type. Returns a new reference.
PyObject* make_lstr_from_pystr(PyObject *py_str) {
    if (!PyUnicode_Check(py_str)) {
        PyErr_SetString(PyExc_TypeError, "py_str must be a str");
        return nullptr;
    }
    cppy::ptr mod( PyImport_ImportModule("lstring") );
    if (!mod) return nullptr;
    cppy::ptr LType( PyObject_GetAttrString(mod.get(), "L") );
    if (!LType) return nullptr;
    // Call the two-arg version using borrowed pointer from LType.
    return make_lstr_from_pystr((PyTypeObject*)LType.get(), py_str);
}

// Return a new reference to the lstring.L type (named lstr here).
PyObject* get_string_lstr_type() {
    cppy::ptr mod( PyImport_ImportModule("_lstring") );
    if (!mod) return nullptr;
    cppy::ptr LType( PyObject_GetAttrString(mod.get(), "L") );
    if (!LType) return nullptr;
    // return a new reference
    return LType.release();
}
