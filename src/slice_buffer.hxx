#ifndef SLICE_BUFFER_HXX
#define SLICE_BUFFER_HXX

#include <Python.h>
#include <stdexcept>
#include <cstdint>
#include <algorithm>
using namespace std;

#include "lstring.hxx"
#include "buffer.hxx"

// ============================================================
// Slice1Buffer — continuous slice with step = 1
// ============================================================
class Slice1Buffer : public Buffer {
private:
    PyObject *lstr_obj;
    Py_ssize_t start_index;
    Py_ssize_t end_index;

public:
    Slice1Buffer(PyObject *lstr, Py_ssize_t start, Py_ssize_t end)
        : lstr_obj(lstr), start_index(start), end_index(end) {
        Py_INCREF(lstr_obj);
    }

    ~Slice1Buffer() override { Py_XDECREF(lstr_obj); }

    Py_ssize_t length() const override {
        return end_index > start_index ? (end_index - start_index) : 0;
    }

    int unicode_kind() const override {
        Buffer *buf = get_buffer(lstr_obj);
        return buf->unicode_kind();
    }

    uint32_t value(Py_ssize_t index) const override {
        Buffer *buf = get_buffer(lstr_obj);
        return buf->value(start_index + index);
    }

    void copy(uint32_t *target, Py_ssize_t start, Py_ssize_t count) const override {
        Buffer *buf = get_buffer(lstr_obj);
        buf->copy(target, start_index + start, count);
    }
    void copy(uint16_t *target, Py_ssize_t start, Py_ssize_t count) const override {
        Buffer *buf = get_buffer(lstr_obj);
        buf->copy(target, start_index + start, count);
    }
    void copy(uint8_t *target, Py_ssize_t start, Py_ssize_t count) const override {
        Buffer *buf = get_buffer(lstr_obj);
        buf->copy(target, start_index + start, count);
    }

    PyObject* repr() const override {
        Buffer *buf = get_buffer(lstr_obj);
        PyObject *inner = buf->repr();
        if (!inner) return nullptr;

        PyObject *result = PyUnicode_FromFormat("%U[%zd:%zd]", inner, start_index, end_index);
        Py_DECREF(inner);
        return result;
    }
};

// ============================================================
// SliceBuffer — slice with arbitrary step (positive or negative)
// ============================================================
class SliceBuffer : public Buffer {
private:
    PyObject *lstr_obj;
    Py_ssize_t start_index;
    Py_ssize_t end_index;
    Py_ssize_t step;
    Py_ssize_t cached_len;

    static inline Py_ssize_t compute_len(Py_ssize_t start, Py_ssize_t end, Py_ssize_t step) {
        if (step > 0) {
            if (start >= end) return 0;
            return (end - start + step - 1) / step;
        } else {
            if (start <= end) return 0;
            long neg_step = -step;
            return (start - end + neg_step - 1) / neg_step;
        }
    }

public:
    SliceBuffer(PyObject *lstr, Py_ssize_t start, Py_ssize_t end, Py_ssize_t step_val)
        : lstr_obj(lstr), start_index(start), end_index(end), step(step_val) {
        if (step == 0) throw runtime_error("SliceBuffer: step cannot be zero");

        cached_len = compute_len(start_index, end_index, step);

        Py_INCREF(lstr_obj);
    }

    ~SliceBuffer() override { Py_XDECREF(lstr_obj); }

    Py_ssize_t length() const override { return cached_len; }

    int unicode_kind() const override {
        Buffer *buf = get_buffer(lstr_obj);
        return buf->unicode_kind();
    }

    uint32_t value(Py_ssize_t index) const override {
        Buffer *buf = get_buffer(lstr_obj);
        return buf->value(start_index + index * step);
    }

    void copy(uint32_t *target, Py_ssize_t start, Py_ssize_t count) const override {
        Buffer *buf = get_buffer(lstr_obj);
        for (Py_ssize_t i = 0; i < count; ++i) {
            target[i] = buf->value(start_index + (start + i) * step);
        }
    }
    void copy(uint16_t *target, Py_ssize_t start, Py_ssize_t count) const override {
        Buffer *buf = get_buffer(lstr_obj);
        for (Py_ssize_t i = 0; i < count; ++i) {
            target[i] = static_cast<uint16_t>(buf->value(start_index + (start + i) * step));
        }
    }
    void copy(uint8_t *target, Py_ssize_t start, Py_ssize_t count) const override {
        Buffer *buf = get_buffer(lstr_obj);
        for (Py_ssize_t i = 0; i < count; ++i) {
            target[i] = static_cast<uint8_t>(buf->value(start_index + (start + i) * step));
        }
    }

    PyObject* repr() const override {
        Buffer *buf = get_buffer(lstr_obj);
        PyObject *inner = buf->repr();
        if (!inner) return nullptr;

        PyObject *result = PyUnicode_FromFormat("%U[%zd:%zd:%ld]", inner, start_index, end_index, step);
        Py_DECREF(inner);
        return result;
    }
};

#endif // SLICE_BUFFER_HXX
