#ifndef STR_BUFFER_HXX
#define STR_BUFFER_HXX

#include <Python.h>
#include <cstdint>
#include <cstring>
#include <cppy/ptr.h>

#include "buffer.hxx"

/**
 * @brief StrBuffer base class (backed by a Python str)
 *
 * Provides read-only accessors to a Python string object and serves as the
 * foundation for Str8/16/32 optimizations.
 */
class StrBuffer : public Buffer {
protected:
    cppy::ptr py_str;

public:
    /**
     * @brief Construct a StrBuffer from a Python Unicode object.
     * @param str A Python unicode object (PyObject*). The constructor
     *            will take ownership via an owning cppy::ptr wrapper.
     */
    StrBuffer(PyObject *str) : py_str(str, true) {}

    /**
     * @brief Default virtual destructor.
     */
    ~StrBuffer() override = default;

    /**
     * @brief Return the number of Unicode code points in the buffer.
     * @return length as Py_ssize_t
     */
    Py_ssize_t length() const override {
        return PyUnicode_GET_LENGTH(py_str.get());
    }

    /**
     * @brief Return the Unicode code point value at the given index.
     * @param index Index of the code point to read (0-based).
     * @return Unicode code point as uint32_t.
     * @throws std::out_of_range if index is invalid.
     */
    uint32_t value(Py_ssize_t index) const override {
        if (index < 0 || index >= length()) throw std::out_of_range("StrBuffer: index out of range");
        return PyUnicode_READ_CHAR(py_str.get(), index);
    }

    /**
     * @brief Copy code points into a 32-bit target buffer.
     *
     * Default implementation reads characters one-by-one. Derived classes
     * may override with optimized memcpy-based paths when the internal
     * representation permits.
     * @param target Destination buffer of uint32_t entries.
     * @param start Start index in source buffer.
     * @param count Number of code points to copy.
     */
    void copy(uint32_t *target, Py_ssize_t start, Py_ssize_t count) const override {
        for (Py_ssize_t i = 0; i < count; ++i) {
            target[i] = PyUnicode_READ_CHAR(py_str.get(), start + i);
        }
    }

    /**
     * @brief Copy code points into a 16-bit target buffer.
     * @param target Destination buffer of uint16_t entries.
     * @param start Start index in source buffer.
     * @param count Number of code points to copy.
     */
    void copy(uint16_t *target, Py_ssize_t start, Py_ssize_t count) const override {
        for (Py_ssize_t i = 0; i < count; ++i) {
            target[i] = static_cast<uint16_t>(PyUnicode_READ_CHAR(py_str.get(), start + i));
        }
    }

    /**
     * @brief Copy code points into an 8-bit target buffer.
     * @param target Destination buffer of uint8_t entries.
     * @param start Start index in source buffer.
     * @param count Number of code points to copy.
     */
    void copy(uint8_t *target, Py_ssize_t start, Py_ssize_t count) const override {
        for (Py_ssize_t i = 0; i < count; ++i) {
            target[i] = static_cast<uint8_t>(PyUnicode_READ_CHAR(py_str.get(), start + i));
        }
    }

    /**
     * @brief Return a Python-level representation of this buffer.
     * @return New reference to a PyObject containing the representation, or
     *         nullptr on error.
     */
    PyObject* repr() const override {
        cppy::ptr repr_obj( py_str.repr() );
        if (!repr_obj) return nullptr;
        return PyUnicode_FromFormat("L%U", repr_obj.get());
    }

    /**
     * @brief Indicate that this buffer represents a string.
     * @return true (always for StrBuffer).
     */
    bool is_str() const override {
        return true;
    }

    /**
     * @brief Access the underlying Python str object.
     * @return Borrowed PyObject* pointing to the Python Unicode object.
     */
    PyObject* get_str() const {
        return py_str.get();
    }

    /**
     * @brief Find a single code point in the wrapped Python string.
     *
     * Uses PyUnicode_FindChar which understands Python slice semantics and
     * is implemented efficiently in CPython. start/end are used as given.
     */
    Py_ssize_t findc(Py_ssize_t start, Py_ssize_t end, uint32_t ch) const override {
        PyObject *s = py_str.get();
        return PyUnicode_FindChar(s, (Py_UCS4)ch, start, end, 1);
    }

    /**
     * @brief Find a single code point searching from the right.
     */
    Py_ssize_t rfindc(Py_ssize_t start, Py_ssize_t end, uint32_t ch) const override {
        PyObject *s = py_str.get();
        return PyUnicode_FindChar(s, (Py_UCS4)ch, start, end, -1);
    }

    /**
     * @brief Specialized comparison for StrBuffer.
     *
     * If the other buffer is also a string (is_str() == true), use
     * PyUnicode_Compare for efficient Python string comparison.
     * Otherwise, fall back to the base class implementation.
     *
     * @param other Other buffer to compare with.
     * @return -1 if *this < other, 0 if equal, 1 if *this > other.
     */
    int cmp(const Buffer* other) const override {
        if (other->is_str()) {
            // Both are Python strings, use PyUnicode_Compare
            const StrBuffer* other_str = static_cast<const StrBuffer*>(other);
            return PyUnicode_Compare(get_str(), other_str->get_str());
        }
        // Fall back to base class implementation
        return Buffer::cmp(other);
    }
};

/**
 * @brief Buffer specialized for 1-byte (UCS1) Python Unicode objects.
 *
 * Provides optimized fast-paths for copying when the internal representation
 * uses a single byte per code point.
 */
class Str8Buffer : public StrBuffer {
public:
    /**
     * @brief Construct a Str8Buffer wrapping a Python unicode object.
     * @param str Python unicode object (PyObject*).
     */
    Str8Buffer(PyObject *str) : StrBuffer(str) {}

    /**
     * @brief Return the Python internal unicode kind for this buffer.
     * @return PyUnicode_1BYTE_KIND
     */
    int unicode_kind() const override {
        return PyUnicode_1BYTE_KIND;
    }

    /**
     * @brief Optimized copy into an 8-bit destination when layout is 1-byte.
     * @param target Destination buffer of uint8_t entries.
     * @param start Start index in source buffer.
     * @param count Number of code points to copy.
     */
    void copy(uint8_t *target, Py_ssize_t start, Py_ssize_t count) const override {
        const uint8_t *src = as_ucs1(py_str.get()) + start;
        std::memcpy(target, src, count * sizeof(uint8_t));
    }
};

/**
 * @brief Buffer specialized for 2-byte (UCS2) Python Unicode objects.
 *
 * Provides optimized memcpy-based copy when the Python string uses a
 * 2-byte internal representation.
 */
class Str16Buffer : public StrBuffer {
public:
    /**
     * @brief Construct a Str16Buffer wrapping a Python unicode object.
     * @param str Python unicode object (PyObject*).
     */
    Str16Buffer(PyObject *str) : StrBuffer(str) {}

    /**
     * @brief Return the Python internal unicode kind for this buffer.
     * @return PyUnicode_2BYTE_KIND
     */
    int unicode_kind() const override {
        return PyUnicode_2BYTE_KIND;
    }

    /**
     * @brief Optimized copy into a 16-bit destination when layout is 2-byte.
     * @param target Destination buffer of uint16_t entries.
     * @param start Start index in source buffer.
     * @param count Number of code points to copy.
     */
    void copy(uint16_t *target, Py_ssize_t start, Py_ssize_t count) const override {
        const uint16_t *src = as_ucs2(py_str.get()) + start;
        std::memcpy(target, src, count * sizeof(uint16_t));
    }
};

/**
 * @brief Buffer specialized for 4-byte (UCS4) Python Unicode objects.
 *
 * Provides optimized memcpy-based copy when the Python string uses a
 * 4-byte internal representation.
 */
class Str32Buffer : public StrBuffer {
public:
    /**
     * @brief Construct a Str32Buffer wrapping a Python unicode object.
     * @param str Python unicode object (PyObject*).
     */
    Str32Buffer(PyObject *str) : StrBuffer(str) {}

    /**
     * @brief Return the Python internal unicode kind for this buffer.
     * @return PyUnicode_4BYTE_KIND
     */
    int unicode_kind() const override {
        return PyUnicode_4BYTE_KIND;
    }

    /**
     * @brief Optimized copy into a 32-bit destination when layout is 4-byte.
     * @param target Destination buffer of uint32_t entries.
     * @param start Start index in source buffer.
     * @param count Number of code points to copy.
     */
    void copy(uint32_t *target, Py_ssize_t start, Py_ssize_t count) const override {
        const uint32_t *src = as_ucs4(py_str.get()) + start;
        std::memcpy(target, src, count * sizeof(uint32_t));
    }
};

#endif // STR_BUFFER_HXX
