#ifndef SLICE_BUFFER_HXX
#define SLICE_BUFFER_HXX

#include <Python.h>
#include <stdexcept>
#include <cstdint>

#include "lstring.hxx"
#include "buffer.hxx"
#include <cppy/ptr.h>

// ============================================================
// Slice1Buffer — continuous slice with step = 1
// ============================================================
class Slice1Buffer : public Buffer {
private:
    cppy::ptr lstr_obj;
    Py_ssize_t start_index;
    Py_ssize_t end_index;

public:
    Slice1Buffer(PyObject *lstr, Py_ssize_t start, Py_ssize_t end)
        : lstr_obj(lstr, true), start_index(start), end_index(end) {
    }

    ~Slice1Buffer() override = default;

    Py_ssize_t length() const override {
        return end_index > start_index ? (end_index - start_index) : 0;
    }

    int unicode_kind() const override {
        Buffer *buf = get_buffer(lstr_obj.get());
        return buf->unicode_kind();
    }

    uint32_t value(Py_ssize_t index) const override {
        Buffer *buf = get_buffer(lstr_obj.get());
        return buf->value(start_index + index);
    }

    void copy(uint32_t *target, Py_ssize_t start, Py_ssize_t count) const override {
        Buffer *buf = get_buffer(lstr_obj.get());
        buf->copy(target, start_index + start, count);
    }
    void copy(uint16_t *target, Py_ssize_t start, Py_ssize_t count) const override {
        Buffer *buf = get_buffer(lstr_obj.get());
        buf->copy(target, start_index + start, count);
    }
    void copy(uint8_t *target, Py_ssize_t start, Py_ssize_t count) const override {
        Buffer *buf = get_buffer(lstr_obj.get());
        buf->copy(target, start_index + start, count);
    }

    PyObject* repr() const override {
        Buffer *buf = get_buffer(lstr_obj.get());
        cppy::ptr inner( buf->repr() );
        if (!inner) return nullptr;
        PyObject *result = PyUnicode_FromFormat("%U[%zd:%zd]", inner.get(), start_index, end_index);
        return result;
    }
};

// ============================================================
// SliceBuffer — slice with arbitrary step (positive or negative)
// ============================================================
class SliceBuffer : public Buffer {
private:
    cppy::ptr lstr_obj;
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
        : lstr_obj(lstr, true), start_index(start), end_index(end), step(step_val) {
        if (step == 0) throw std::runtime_error("SliceBuffer: step cannot be zero");

        cached_len = compute_len(start_index, end_index, step);
    }

    ~SliceBuffer() override = default;

    Py_ssize_t length() const override { return cached_len; }

    int unicode_kind() const override {
        Buffer *buf = get_buffer(lstr_obj.get());
        return buf->unicode_kind();
    }

    uint32_t value(Py_ssize_t index) const override {
        Buffer *buf = get_buffer(lstr_obj.get());
        return buf->value(start_index + index * step);
    }

    void copy(uint32_t *target, Py_ssize_t start, Py_ssize_t count) const override {
        Buffer *buf = get_buffer(lstr_obj.get());
        for (Py_ssize_t i = 0; i < count; ++i) {
            target[i] = buf->value(start_index + (start + i) * step);
        }
    }
    void copy(uint16_t *target, Py_ssize_t start, Py_ssize_t count) const override {
        Buffer *buf = get_buffer(lstr_obj.get());
        for (Py_ssize_t i = 0; i < count; ++i) {
            target[i] = static_cast<uint16_t>(buf->value(start_index + (start + i) * step));
        }
    }
    void copy(uint8_t *target, Py_ssize_t start, Py_ssize_t count) const override {
        Buffer *buf = get_buffer(lstr_obj.get());
        for (Py_ssize_t i = 0; i < count; ++i) {
            target[i] = static_cast<uint8_t>(buf->value(start_index + (start + i) * step));
        }
    }

    PyObject* repr() const override {
        Buffer *buf = get_buffer(lstr_obj.get());
        cppy::ptr inner( buf->repr() );
        if (!inner) return nullptr;
        PyObject *result = PyUnicode_FromFormat("%U[%zd:%zd:%ld]", inner.get(), start_index, end_index, step);
        return result;
    }
};

#endif // SLICE_BUFFER_HXX
