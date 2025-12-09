#ifndef STR_BUFFER_HXX
#define STR_BUFFER_HXX

#include <Python.h>
#include <cstdint>
#include <cstring>
#include <cppy/ptr.h>

#include "buffer.hxx"

// ============================================================
// StrBuffer (base for Str*Buffer)
// ============================================================
// intermediate wrapper using cppy ptr to manage refcounting safely
class StrBuffer : public Buffer {
protected:
    cppy::ptr py_str;

public:
    StrBuffer(PyObject *str) : py_str(str, true) {}
    ~StrBuffer() override = default;

    Py_ssize_t length() const override {
        return PyUnicode_GET_LENGTH(py_str.get());
    }

    // default unicode_kind left abstract - implemented by derived classes

    uint32_t value(Py_ssize_t index) const override {
        if (index < 0 || index >= length()) throw std::out_of_range("StrBuffer: index out of range");
        return PyUnicode_READ_CHAR(py_str.get(), index);
    }

    // Default copy implementations use per-character reads; derived classes
    // may override with memcpy-based fast paths when data layout allows.
    void copy(uint32_t *target, Py_ssize_t start, Py_ssize_t count) const override {
        for (Py_ssize_t i = 0; i < count; ++i) {
            target[i] = PyUnicode_READ_CHAR(py_str.get(), start + i);
        }
    }
    void copy(uint16_t *target, Py_ssize_t start, Py_ssize_t count) const override {
        for (Py_ssize_t i = 0; i < count; ++i) {
            target[i] = static_cast<uint16_t>(PyUnicode_READ_CHAR(py_str.get(), start + i));
        }
    }
    void copy(uint8_t *target, Py_ssize_t start, Py_ssize_t count) const override {
        for (Py_ssize_t i = 0; i < count; ++i) {
            target[i] = static_cast<uint8_t>(PyUnicode_READ_CHAR(py_str.get(), start + i));
        }
    }

    PyObject* repr() const override {
        PyObject *repr_obj = py_str.repr();
        if (!repr_obj) {
            return nullptr;
        }
        PyObject *result = PyUnicode_FromFormat("l%U", repr_obj);
        Py_DECREF(repr_obj);
        return result;
    }
};

// ============================================================
// Str8Buffer
// ============================================================
class Str8Buffer : public StrBuffer {
public:
    Str8Buffer(PyObject *str) : StrBuffer(str) {}

    int unicode_kind() const override {
        return PyUnicode_1BYTE_KIND;
    }

    // optimized copy for 1-byte layout
    void copy(uint8_t *target, Py_ssize_t start, Py_ssize_t count) const override {
        const uint8_t *src = as_ucs1(py_str.get()) + start;
        std::memcpy(target, src, count * sizeof(uint8_t));
    }
};

// ============================================================
// Str16Buffer
// ============================================================
class Str16Buffer : public StrBuffer {
public:
    Str16Buffer(PyObject *str) : StrBuffer(str) {}

    int unicode_kind() const override {
        return PyUnicode_2BYTE_KIND;
    }

    // optimized copy for 2-byte layout
    void copy(uint16_t *target, Py_ssize_t start, Py_ssize_t count) const override {
        const uint16_t *src = as_ucs2(py_str.get()) + start;
        std::memcpy(target, src, count * sizeof(uint16_t));
    }
};

// ============================================================
// Str32Buffer
// ============================================================
class Str32Buffer : public StrBuffer {
public:
    Str32Buffer(PyObject *str) : StrBuffer(str) {}

    int unicode_kind() const override {
        return PyUnicode_4BYTE_KIND;
    }

    // optimized copy for 4-byte layout
    void copy(uint32_t *target, Py_ssize_t start, Py_ssize_t count) const override {
        const uint32_t *src = as_ucs4(py_str.get()) + start;
        std::memcpy(target, src, count * sizeof(uint32_t));
    }
};

#endif // STR_BUFFER_HXX
