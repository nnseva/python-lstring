#ifndef MUL_BUFFER_HXX
#define MUL_BUFFER_HXX

#include <Python.h>
#include <stdexcept>
#include <cstdint>

#include "buffer.hxx"
#include <cppy/ptr.h>

/**
 * @brief MulBuffer — string repetition
 *
 * Represents repeating a buffer a fixed number of times without copying.
 */
class MulBuffer : public Buffer {
private:
    cppy::ptr lstr_obj;
    Py_ssize_t repeat_count;

public:
    /**
     * @brief Construct a repetition buffer that repeats `lstr` `count` times.
     *
     * @param lstr Python object that implements a Buffer (borrowed ref).
     * @param count Number of repetitions (must be non-negative).
     * @throws std::runtime_error if count is negative.
     */
    MulBuffer(PyObject *lstr, Py_ssize_t count)
        : lstr_obj(lstr, true), repeat_count(count) 
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
        Buffer *buf = get_buffer(lstr_obj.get());
        return buf->length() * repeat_count;
    }

    /**
     * @brief Unicode storage kind required for the buffer.
     *
     * Delegates to the underlying base buffer.
     */
    int unicode_kind() const override {
        Buffer *buf = get_buffer(lstr_obj.get());
        return buf->unicode_kind();
    }

    /**
     * @brief Return code point at index in the repeated view.
     *
     * Maps the global index to the base buffer using modulo arithmetic.
     * Throws std::out_of_range if the base buffer has zero length.
     */
    uint32_t value(Py_ssize_t index) const override {
        Buffer *buf = get_buffer(lstr_obj.get());
        Py_ssize_t base_len = buf->length();
        if (base_len <= 0) throw std::out_of_range("MulBuffer: base length is zero");
        Py_ssize_t pos = index % base_len;
        return buf->value(pos);
    }

    /**
     * @brief Copy a range of code points into a 32-bit destination buffer.
     */
    void copy(uint32_t *target, Py_ssize_t start, Py_ssize_t count) const override {
        Buffer *buf = get_buffer(lstr_obj.get());
        Py_ssize_t base_len = buf->length();
        if (base_len <= 0) return;
        for (Py_ssize_t i = 0; i < count; ++i) {
            target[i] = buf->value((start + i) % base_len);
        }
    }
    /**
     * @brief Copy a range of code points into a 16-bit destination buffer.
     */
    void copy(uint16_t *target, Py_ssize_t start, Py_ssize_t count) const override {
        Buffer *buf = get_buffer(lstr_obj.get());
        Py_ssize_t base_len = buf->length();
        if (base_len <= 0) return;
        for (Py_ssize_t i = 0; i < count; ++i) {
            target[i] = static_cast<uint16_t>(buf->value((start + i) % base_len));
        }
    }

    /**
     * @brief Copy a range of code points into an 8-bit destination buffer.
     */
    void copy(uint8_t *target, Py_ssize_t start, Py_ssize_t count) const override {
        Buffer *buf = get_buffer(lstr_obj.get());
        Py_ssize_t base_len = buf->length();
        if (base_len <= 0) return;
        for (Py_ssize_t i = 0; i < count; ++i) {
            target[i] = static_cast<uint8_t>(buf->value((start + i) % base_len));
        }
    }

    /**
     * @brief Produce a Python-level repr for the repeated buffer.
     *
     * Returns a new Python string of the form "(<base_repr> * <count>)".
     */
    PyObject* repr() const override {
        Buffer *buf = get_buffer(lstr_obj.get());
        cppy::ptr lrepr( buf->repr() );
        if (!lrepr) return nullptr;
        PyObject *result = PyUnicode_FromFormat("(%U * %zd)", lrepr.get(), repeat_count);
        return result;
    }
};

#endif // MUL_BUFFER_HXX
