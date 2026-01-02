#ifndef MUL_BUFFER_HXX
#define MUL_BUFFER_HXX

#include <Python.h>
#include <stdexcept>
#include <cstdint>

#include "buffer.hxx"
#include "lstring.hxx"
#include "tptr.hxx"
#include <cppy/ptr.h>

/**
 * @brief MulBuffer — string repetition
 *
 * Represents repeating a buffer a fixed number of times without copying.
 */
class MulBuffer : public Buffer {
private:
    tptr<LStrObject> lstr_obj;
    Py_ssize_t repeat_count;

public:
    /**
     * @brief Construct a repetition buffer that repeats `L` `count` times.
     *
     * @param L Python object that implements a Buffer (borrowed ref).
     * @param count Number of repetitions (must be non-negative).
     * @throws std::runtime_error if count is negative.
     */
    MulBuffer(PyObject *lstr, Py_ssize_t count)
        : lstr_obj((LStrObject*)lstr, true), repeat_count(count) 
    {
        if (repeat_count < 0) {
            throw std::runtime_error("MulBuffer: repeat count must be non-negative");
        }
    }

    /**
     * @brief Destructor (defaulted).
     */
    ~MulBuffer() override = default;

    /**
     * @brief Total length of the repeated buffer.
     *
     * Returns base_length * repeat_count.
     */
    Py_ssize_t length() const override {
        return lstr_obj->buffer->length() * repeat_count;
    }

    /**
     * @brief Unicode storage kind required for the buffer.
     *
     * Delegates to the underlying base buffer.
     */
    int unicode_kind() const override {
        return lstr_obj->buffer->unicode_kind();
    }

    /**
     * @brief Return code point at index in the repeated view.
     *
     * Maps the global index to the base buffer using modulo arithmetic.
     * Throws std::out_of_range if the base buffer has zero length.
     */
    uint32_t value(Py_ssize_t index) const override {
        Py_ssize_t base_len = lstr_obj->buffer->length();
        if (base_len <= 0) throw std::out_of_range("MulBuffer: base length is zero");
        Py_ssize_t pos = index % base_len;
        return lstr_obj->buffer->value(pos);
    }

    /**
     * @brief Copy a range of code points into a 32-bit destination buffer.
     */
    void copy(uint32_t *target, Py_ssize_t start, Py_ssize_t count) const override {
        Py_ssize_t base_len = lstr_obj->buffer->length();
        if (base_len <= 0) return;
        for (Py_ssize_t i = 0; i < count; ++i) {
            target[i] = lstr_obj->buffer->value((start + i) % base_len);
        }
    }
    /**
     * @brief Copy a range of code points into a 16-bit destination buffer.
     */
    void copy(uint16_t *target, Py_ssize_t start, Py_ssize_t count) const override {
        Py_ssize_t base_len = lstr_obj->buffer->length();
        if (base_len <= 0) return;
        for (Py_ssize_t i = 0; i < count; ++i) {
            target[i] = static_cast<uint16_t>(lstr_obj->buffer->value((start + i) % base_len));
        }
    }

    /**
     * @brief Copy a range of code points into an 8-bit destination buffer.
     */
    void copy(uint8_t *target, Py_ssize_t start, Py_ssize_t count) const override {
        Py_ssize_t base_len = lstr_obj->buffer->length();
        if (base_len <= 0) return;
        for (Py_ssize_t i = 0; i < count; ++i) {
            target[i] = static_cast<uint8_t>(lstr_obj->buffer->value((start + i) % base_len));
        }
    }

    /**
     * @brief Produce a Python-level repr for the repeated buffer.
     *
     * Returns a new Python string of the form "(<base_repr> * <count>)".
     */
    PyObject* repr() const override {
        cppy::ptr lrepr( lstr_obj->buffer->repr() );
        if (!lrepr) return nullptr;
        PyObject *result = PyUnicode_FromFormat("(%U * %zd)", lrepr.get(), repeat_count);
        return result;
    }

    Py_ssize_t findc(Py_ssize_t start, Py_ssize_t end, uint32_t ch) const override {
        Py_ssize_t base_len = lstr_obj->buffer->length();
        // total length may overflow if huge, but repeat_count and base_len
        // are expected to be reasonable; still guard against zero base
        if (base_len <= 0) return -1;
        Py_ssize_t total = base_len * repeat_count;

        if (total <= 0) return -1;
        if (start < 0) start = 0;
        if (end < 0) end = 0;
        if (start > total) return -1;
        if (end > total) end = total;
        if (start >= end) return -1;

        // Compute starting repetition and offset within base
        Py_ssize_t rep_start = start / base_len;
        Py_ssize_t off_start = start - rep_start * base_len; // start % base_len
        // Use rep_end = end / base_len as "first repetition entirely beyond range"
        Py_ssize_t rep_end = end / base_len;
        Py_ssize_t off_end = end - rep_end * base_len; // exclusive upper bound within rep_end

        // Three cases:
        // A) rep_end == rep_start -> [start,end) is inside one block
        // B) rep_end == rep_start + 1 -> spans two adjacent blocks
        // C) rep_end >= rep_start + 2 -> at least one full block between

        if (rep_end == rep_start) {
            // single-block: search only within [off_start, off_end)
            Py_ssize_t pos = lstr_obj->buffer->findc(off_start, off_end, ch);
            if (pos != -1) return rep_start * base_len + pos;
            return -1;
        }

        // rep_end > rep_start
        // 1) search first partial segment [off_start, base_len)
        Py_ssize_t pos = lstr_obj->buffer->findc(off_start, base_len, ch);
        if (pos != -1) return rep_start * base_len + pos;

        if (rep_end == rep_start + 1) {
            // adjacent blocks: second block may be partial, search [0, off_end)
            if (off_end > 0) {
                Py_ssize_t pos2 = lstr_obj->buffer->findc(0, off_end, ch);
                if (pos2 != -1) return rep_end * base_len + pos2;
            }
            return -1;
        }

        // rep_end >= rep_start + 2: there exists at least one full block (rep_start+1)
        // that is entirely inside [start,end). We have already searched [off_start, base_len)
        // in the first block, so we only need to search the remaining prefix [0, off_start)
        // of the base block to find the earliest occurrence inside rep_start+1.
        if (off_start > 0) {
            Py_ssize_t pos_in_prefix = lstr_obj->buffer->findc(0, off_start, ch);
            if (pos_in_prefix != -1) return (rep_start + 1) * base_len + pos_in_prefix;
        }

        return -1;
    }

    Py_ssize_t rfindc(Py_ssize_t start, Py_ssize_t end, uint32_t ch) const override {
        Py_ssize_t base_len = lstr_obj->buffer->length();
        if (base_len <= 0) return -1;
        Py_ssize_t total = base_len * repeat_count;

        if (total <= 0) return -1;
        if (start < 0) start = 0;
        if (end < 0) end = 0;
        if (start > total) return -1;
        if (end > total) end = total;
        if (start >= end) return -1;

        // Compute reps and offsets using rep_end = end / base_len
        Py_ssize_t rep_start = start / base_len;
        Py_ssize_t off_start = start - rep_start * base_len;
        Py_ssize_t rep_end = end / base_len;
        Py_ssize_t off_end = end - rep_end * base_len; // exclusive upper bound within rep_end

        // Case A: single block
        if (rep_end == rep_start) {
            Py_ssize_t pos = lstr_obj->buffer->rfindc(off_start, off_end, ch);
            if (pos != -1) return rep_start * base_len + pos;
            return -1;
        }

        // Case B and C: rep_end > rep_start
        // 1) search last partial block [0, off_end) in reverse
        if (off_end > 0) {
            Py_ssize_t pos = lstr_obj->buffer->rfindc(0, off_end, ch);
            if (pos != -1) return rep_end * base_len + pos;
        }

        if (rep_end == rep_start + 1) {
            // adjacent blocks: search first partial block [off_start, base_len)
            Py_ssize_t pos2 = lstr_obj->buffer->rfindc(off_start, base_len, ch);
            if (pos2 != -1) return rep_start * base_len + pos2;
            return -1;
        }

        // rep_end >= rep_start + 2: there is at least one full block between
        // search the suffix of base block that was not yet searched in the final partial
        // Because we already checked final partial and it didn't contain ch, we can
        // search the full base for the rightmost occurrence and map it into rep_end-1.
        Py_ssize_t pos_in_base = lstr_obj->buffer->rfindc(0, base_len, ch);
        if (pos_in_base != -1) {
            return (rep_end - 1) * base_len + pos_in_base;
        }
        return -1;
    }
};

#endif // MUL_BUFFER_HXX
