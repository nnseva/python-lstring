#ifndef SLICE_BUFFER_HXX
#define SLICE_BUFFER_HXX

#include <Python.h>
#include <stdexcept>
#include <cstdint>

#include "lstring.hxx"
#include "buffer.hxx"
#include "tptr.hxx"
#include <cppy/ptr.h>

/**
 * @brief Slice1Buffer — continuous slice with step = 1
 *
 * Provides a view for continuous slices (step == 1) over another buffer.
 */
class Slice1Buffer : public Buffer {
protected:
    tptr<LStrObject> lstr_obj;
    Py_ssize_t start_index;
    Py_ssize_t end_index;

    mutable Py_ssize_t cached_kind;

public:
    /**
     * @brief Construct a continuous slice view [start:end) with step == 1.
     *
     * @param lstr Python object that provides a Buffer implementation (borrowed ref).
     * @param start Start index (inclusive) within the base buffer.
     * @param end End index (exclusive) within the base buffer.
     */
    Slice1Buffer(PyObject *lstr, Py_ssize_t start, Py_ssize_t end)
        : lstr_obj((LStrObject*)lstr, true), start_index(start), end_index(end), cached_kind(-1) {
    }

    /**
     * @brief Destructor (defaulted).
     */
    ~Slice1Buffer() override = default;

    /**
     * @brief Length of the continuous slice.
     *
     * Returns max(0, end - start).
     */
    Py_ssize_t length() const override {
        return end_index > start_index ? (end_index - start_index) : 0;
    }

    /**
     * @brief Determine the minimal Unicode storage kind required by this slice.
     *
     * Caches the computed kind in `cached_kind`. If the underlying buffer
     * suggests a larger kind, this function scans the slice to see whether a
     * narrower representation suffices (e.g. all code points fit in 1-byte).
     */
    int unicode_kind() const override {
        if (cached_kind != -1) return cached_kind;

        int original_kind = lstr_obj->buffer->unicode_kind();
        if(original_kind == PyUnicode_1BYTE_KIND) {
            cached_kind = PyUnicode_1BYTE_KIND;
        } else if(original_kind == PyUnicode_2BYTE_KIND) {
            // check if all char are in 1-byte range
            int kind = PyUnicode_1BYTE_KIND;
            for(Py_ssize_t index=0; index < length(); index++) {
                if(value(index) >= 0x100) {
                    kind = PyUnicode_2BYTE_KIND;
                    break;
                }
            }
            cached_kind = kind;
        } else if(original_kind == PyUnicode_4BYTE_KIND) {
            // check if all char are in 1-byte or 2-byte range
            int kind = PyUnicode_1BYTE_KIND;
            for(Py_ssize_t index=0; index < length(); index++) {
                if(value(index) >= 0x10000) {
                    kind = PyUnicode_4BYTE_KIND;
                    break;
                } else if(value(index) >= 0x100) {
                    if(kind < PyUnicode_2BYTE_KIND) {
                        kind = PyUnicode_2BYTE_KIND;
                    }
                }
            }
            cached_kind = kind;
        }
        return cached_kind;
    }

    /**
     * @brief Return the code point at position `index` in the slice.
     *
     * Maps to base buffer position `start_index + index`.
     */
    uint32_t value(Py_ssize_t index) const override {
        return lstr_obj->buffer->value(start_index + index);
    }

    /**
     * @brief Copy a range of code points from the slice into a 32-bit target.
     *
     * Copies `count` code points starting from `start` (relative to the slice)
     * into `target`.
     */
    void copy(uint32_t *target, Py_ssize_t start, Py_ssize_t count) const override {
        lstr_obj->buffer->copy(target, start_index + start, count);
    }
    /**
     * @brief Copy a range of code points into a 16-bit target buffer.
     */
    void copy(uint16_t *target, Py_ssize_t start, Py_ssize_t count) const override {
        lstr_obj->buffer->copy(target, start_index + start, count);
    }
    /**
     * @brief Copy a range of code points into an 8-bit target buffer.
     */
    void copy(uint8_t *target, Py_ssize_t start, Py_ssize_t count) const override {
        lstr_obj->buffer->copy(target, start_index + start, count);
    }

    /**
     * @brief Produce a Python-level repr for the slice (e.g. "<inner>[start:end]").
     */
    PyObject* repr() const override {
        cppy::ptr inner( lstr_obj->buffer->repr() );
        if (!inner) return nullptr;
        return PyUnicode_FromFormat("%U[%zd:%zd]", inner.get(), start_index, end_index);
    }
    
    Py_ssize_t findc(Py_ssize_t start, Py_ssize_t end, uint32_t ch) const override {
        Py_ssize_t len = length();
        if (len <= 0) return -1;
        if (start < 0) start = 0;
        if (end < 0) end = 0;
        if (start > len) return -1;
        if (end > len) end = len;
        if (start >= end) return -1;

        // Map slice-relative range [start, end) to base buffer range [bstart, bend)
        Py_ssize_t bstart = start_index + start;
        Py_ssize_t bend = start_index + end;
        Py_ssize_t pos = lstr_obj->buffer->findc(bstart, bend, ch);
        if (pos == -1) return -1;
        // convert base index back to slice-relative index
        return pos - start_index;
    }

    Py_ssize_t rfindc(Py_ssize_t start, Py_ssize_t end, uint32_t ch) const override {
        Py_ssize_t len = length();
        if (len <= 0) return -1;
        if (start < 0) start = 0;
        if (end < 0) end = 0;
        if (start > len) return -1;
        if (end > len) end = len;
        if (start >= end) return -1;

        Py_ssize_t bstart = start_index + start;
        Py_ssize_t bend = start_index + end;
        Py_ssize_t pos = lstr_obj->buffer->rfindc(bstart, bend, ch);
        if (pos == -1) return -1;
        return pos - start_index;
    }
};
/**
 * @brief SliceBuffer — slice with arbitrary (possibly negative) step.
 *
 * Extends Slice1Buffer to support arbitrary stepping across the base buffer.
 */
class SliceBuffer : public Slice1Buffer {
protected:
    Py_ssize_t step;
    Py_ssize_t cached_len;

    /**
     * @brief Compute the number of items in the arithmetic progression
     *        defined by [start, end) with step `step`.
     *
     * Handles both positive and negative steps. Returns 0 for empty ranges.
     */
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
    /**
     * @brief Construct a slice with arbitrary step.
     *
     * @param lstr Python object providing a Buffer (borrowed ref).
     * @param start Start index (inclusive).
     * @param end End index (exclusive).
     * @param step_val Step value (non-zero).
     * @throws std::runtime_error if step_val is zero.
     */
    SliceBuffer(PyObject *lstr, Py_ssize_t start, Py_ssize_t end, Py_ssize_t step_val)
        : Slice1Buffer(lstr, start, end), step(step_val) {
        if (step == 0) throw std::runtime_error("SliceBuffer: step cannot be zero");
        cached_len = compute_len(start_index, end_index, step);
    }

    /**
     * @brief Destructor (defaulted).
     */
    ~SliceBuffer() override = default;

    /**
     * @brief Length of the strided slice (number of elements when stepping).
     */
    Py_ssize_t length() const override { return cached_len; }

    /**
     * @brief Return the code point at logical index `index` in the strided slice.
     */
    uint32_t value(Py_ssize_t index) const override {
        return lstr_obj->buffer->value(start_index + index * step);
    }

    /**
     * @brief Copy a strided range of code points into a 32-bit target buffer.
     */
    void copy(uint32_t *target, Py_ssize_t start, Py_ssize_t count) const override {
        Buffer *buf = lstr_obj->buffer;
        for (Py_ssize_t i = 0; i < count; ++i) {
            target[i] = buf->value(start_index + (start + i) * step);
        }
    }
    /**
     * @brief Copy a strided range of code points into a 16-bit target buffer.
     */
    void copy(uint16_t *target, Py_ssize_t start, Py_ssize_t count) const override {
        Buffer *buf = lstr_obj->buffer;
        for (Py_ssize_t i = 0; i < count; ++i) {
            target[i] = static_cast<uint16_t>(buf->value(start_index + (start + i) * step));
        }
    }
    /**
     * @brief Copy a strided range of code points into an 8-bit target buffer.
     */
    void copy(uint8_t *target, Py_ssize_t start, Py_ssize_t count) const override {
        Buffer *buf = lstr_obj->buffer;
        for (Py_ssize_t i = 0; i < count; ++i) {
            target[i] = static_cast<uint8_t>(buf->value(start_index + (start + i) * step));
        }
    }

    /**
     * @brief Produce a Python-level repr for the strided slice ("<inner>[start:end:step]").
     */
    PyObject* repr() const override {
        cppy::ptr inner( lstr_obj->buffer->repr() );
        if (!inner) return nullptr;
        return PyUnicode_FromFormat("%U[%zd:%zd:%ld]", inner.get(), start_index, end_index, step);
    }

    Py_ssize_t findc(Py_ssize_t start, Py_ssize_t end, uint32_t ch) const override {
        Py_ssize_t len = length();
        if (len <= 0) return -1;
        if (start < 0) start = 0;
        if (end < 0) end = 0;
        if (start > len) return -1;
        if (end > len) end = len;
        if (start >= end) return -1;

        Buffer *buf = lstr_obj->buffer;
        for (Py_ssize_t i = start; i < end; ++i) {
            uint32_t v = buf->value(start_index + i * step);
            if (v == ch) return i;
        }
        return -1;
    }

    Py_ssize_t rfindc(Py_ssize_t start, Py_ssize_t end, uint32_t ch) const override {
        Py_ssize_t len = length();
        if (len <= 0) return -1;
        if (start < 0) start = 0;
        if (end < 0) end = 0;
        if (start > len) return -1;
        if (end > len) end = len;
        if (start >= end) return -1;

        Buffer *buf = lstr_obj->buffer;
        for (Py_ssize_t i = end - 1; i >= start; --i) {
            uint32_t v = buf->value(start_index + i * step);
            if (v == ch) return i;
        }
        return -1;
    }
};

#endif // SLICE_BUFFER_HXX
