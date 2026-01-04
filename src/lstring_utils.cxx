/**
 * @file lstring_utils.cxx
 * @brief Utility helpers for lstring: buffer creation and optimization helpers.
 */

#include <Python.h>
#include "lstring.hxx"
#include "lstring_utils.hxx"
#include "tptr.hxx"
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

    // Ask the buffer to collapse itself
    Buffer *new_buf = self->buffer->collapse();
    if (!new_buf) {
        // No collapse performed or error occurred
        return;
    }

    // Replace buffer with the collapsed version
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

    // Ask the buffer to optimize itself
    Buffer *new_buf = self->buffer->optimize();
    if (!new_buf) {
        // No optimize performed or error occurred
        return;
    }

    // Replace buffer with the optimized version
    delete self->buffer;
    self->buffer = new_buf;
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

    tptr<LStrObject> self((LStrObject*)type->tp_alloc(type, 0));
    if (!self) return nullptr;

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

    return self.ptr().release();
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

/**
 * @brief Create a new Python str from Buffer contents.
 *
 * Materializes the buffer into a concrete Python unicode object.
 * If the buffer already wraps a Python str (StrBuffer), returns it
 * directly with an owned reference to avoid copying.
 *
 * @param buf Buffer to convert (borrowed reference)
 * @return New reference to PyObject* (str) or nullptr on error.
 */
PyObject* buffer_to_pystr(const Buffer* buf) {
    if (!buf) {
        PyErr_SetString(PyExc_ValueError, "Cannot convert nullptr buffer to str");
        return nullptr;
    }

    // Shortcut: if buffer already wraps a Python str (StrBuffer), return it
    // directly (with an owned reference) to avoid copying.
    if (buf->is_str()) {
        // Safe to static_cast because StrBuffer overrides is_str()
        const StrBuffer *sbuf = static_cast<const StrBuffer*>(buf);
        return cppy::incref(sbuf->get_str());
    }

    uint32_t len = buf->length();
    int kind = buf->unicode_kind();

    PyObject *py_str = nullptr;
    if (kind == PyUnicode_1BYTE_KIND) {
        py_str = PyUnicode_New(len, 0xFF);
        if (!py_str) return nullptr;
        uint8_t *data = reinterpret_cast<uint8_t*>(PyUnicode_DATA(py_str));
        buf->copy(data, 0, len);
    } else if (kind == PyUnicode_2BYTE_KIND) {
        py_str = PyUnicode_New(len, 0xFFFF);
        if (!py_str) return nullptr;
        uint16_t *data = reinterpret_cast<uint16_t*>(PyUnicode_DATA(py_str));
        buf->copy(data, 0, len);
    } else if (kind == PyUnicode_4BYTE_KIND) {
        py_str = PyUnicode_New(len, 0x10FFFF);
        if (!py_str) return nullptr;
        uint32_t *data = reinterpret_cast<uint32_t*>(PyUnicode_DATA(py_str));
        buf->copy(data, 0, len);
    } else {
        PyErr_SetString(PyExc_RuntimeError, "Unsupported buffer kind");
        return nullptr;
    }

    return py_str;
}
