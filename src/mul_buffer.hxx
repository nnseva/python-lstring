#ifndef MUL_BUFFER_HXX
#define MUL_BUFFER_HXX

#include <Python.h>
#include <stdexcept>
#include <cstdint>
#include <string>

#include "buffer.hxx"

// ============================================================
// MulBuffer — повторение строки
// ============================================================
class MulBuffer : public Buffer {
private:
    PyObject *lstr_obj;
    PyObject *count_obj;
    Py_ssize_t repeat_count;

public:
    MulBuffer(PyObject *lstr, PyObject *count)
        : lstr_obj(lstr), count_obj(count) {
        Py_INCREF(lstr_obj);
        Py_INCREF(count_obj);

        repeat_count = PyLong_AsSsize_t(count_obj);
        if (repeat_count < 0) {
            throw std::runtime_error("MulBuffer: repeat count must be non-negative");
        }
    }

    ~MulBuffer() override {
        Py_XDECREF(lstr_obj);
        Py_XDECREF(count_obj);
    }

    Py_ssize_t length() const override {
        Buffer *buf = get_buffer(lstr_obj);
        return buf->length() * repeat_count;
    }

    int unicode_kind() const override {
        Buffer *buf = get_buffer(lstr_obj);
        return buf->unicode_kind();
    }

    uint32_t value(Py_ssize_t index) const override {
        Buffer *buf = get_buffer(lstr_obj);
        Py_ssize_t base_len = buf->length();
        if (base_len == 0) throw std::out_of_range("MulBuffer: base length is zero");
        Py_ssize_t pos = index % base_len;
        return buf->value(pos);
    }

    void copy(uint32_t *target, Py_ssize_t start, Py_ssize_t count) const override {
        Buffer *buf = get_buffer(lstr_obj);
        Py_ssize_t base_len = buf->length();
        for (Py_ssize_t i = 0; i < count; ++i) {
            target[i] = buf->value((start + i) % base_len);
        }
    }
    void copy(uint16_t *target, Py_ssize_t start, Py_ssize_t count) const override {
        Buffer *buf = get_buffer(lstr_obj);
        Py_ssize_t base_len = buf->length();
        for (Py_ssize_t i = 0; i < count; ++i) {
            target[i] = static_cast<uint16_t>(buf->value((start + i) % base_len));
        }
    }
    void copy(uint8_t *target, Py_ssize_t start, Py_ssize_t count) const override {
        Buffer *buf = get_buffer(lstr_obj);
        Py_ssize_t base_len = buf->length();
        for (Py_ssize_t i = 0; i < count; ++i) {
            target[i] = static_cast<uint8_t>(buf->value((start + i) % base_len));
        }
    }

    // ---------- repr ----------
    PyObject* repr() const override {
        Buffer *buf = get_buffer(lstr_obj);
        PyObject *lrepr = buf->repr();
        if (!lrepr) return nullptr;

        PyObject *result = PyUnicode_FromFormat("(%U * %zd)", lrepr, repeat_count);
        Py_DECREF(lrepr);
        return result;
    }
};

#endif // MUL_BUFFER_HXX
