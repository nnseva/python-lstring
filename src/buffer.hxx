#ifndef BUFFER_HXX
#define BUFFER_HXX

#include <Python.h>
#include <stdexcept>
#include <cstdint>
#include <cstring>

#include "lstring.hxx"

/**
 * @brief Abstract Buffer base class
 *
 * Provides the virtual API for buffer-backed lazy string implementations.
 */
class Buffer {
protected:

    /**
     * @brief Inline helper to treat PyUnicode_DATA as 1-byte storage.
     * @param s Python unicode object.
     * @return pointer to ucs1 data.
     */
    inline const uint8_t* as_ucs1(PyObject* s) const {
        return reinterpret_cast<const uint8_t*>(PyUnicode_DATA(s));
    }
    /**
     * @brief Inline helper to treat PyUnicode_DATA as 2-byte storage.
     * @param s Python unicode object.
     * @return pointer to ucs2 data.
     */
    inline const uint16_t* as_ucs2(PyObject* s) const {
        return reinterpret_cast<const uint16_t*>(PyUnicode_DATA(s));
    }

    /**
     * @brief Inline helper to treat PyUnicode_DATA as 4-byte storage.
     * @param s Python unicode object.
     * @return pointer to ucs4 data.
     */
    inline const uint32_t* as_ucs4(PyObject* s) const {
        return reinterpret_cast<const uint32_t*>(PyUnicode_DATA(s));
    }

    Py_hash_t cached_hash;  // cache for computed hash

public:
    /**
     * @brief Construct an empty Buffer with a cleared cached hash.
     */
    Buffer() : cached_hash(-1) {}

    /**
     * @brief Virtual destructor.
     */
    virtual ~Buffer() {}

    /**
     * @brief Return the number of code points in the buffer.
     */
    virtual Py_ssize_t length() const = 0;

    /**
     * @brief Return the Python unicode kind (1/2/4 byte) used by this buffer.
     */
    virtual int unicode_kind() const = 0;

    /**
     * @brief Read the code point value at `index`.
     * @param index Position to read (0-based).
     * @return Unicode code point as uint32_t.
     */
    virtual uint32_t value(Py_ssize_t index) const = 0;

    /**
     * @brief Copy code points into a 32-bit target buffer.
     * @param target Destination buffer of uint32_t entries.
     * @param start Start index in source buffer.
     * @param count Number of code points to copy.
     */
    virtual void copy(uint32_t *target, Py_ssize_t start, Py_ssize_t count) const = 0;

    /**
     * @brief Copy code points into a 16-bit target buffer.
     * @param target Destination buffer of uint16_t entries.
     * @param start Start index in source buffer.
     * @param count Number of code points to copy.
     */
    virtual void copy(uint16_t *target, Py_ssize_t start, Py_ssize_t count) const = 0;

    /**
     * @brief Copy code points into an 8-bit target buffer.
     * @param target Destination buffer of uint8_t entries.
     * @param start Start index in source buffer.
     * @param count Number of code points to copy.
     */
    virtual void copy(uint8_t *target, Py_ssize_t start, Py_ssize_t count) const = 0;

    /**
     * @brief Produce a Python-level representation for debugging/repr.
     * @return New reference to PyObject* or nullptr on error.
     */
    virtual PyObject* repr() const = 0;

    /**
     * @brief Indicate whether this buffer is a StrBuffer wrapping a Python str.
     * @return false by default; overridden by StrBuffer.
     */
    virtual bool is_str() const {
        return false;
    }

    /**
     * @brief Find a single code point in the buffer searching forward.
     *
     * Searches for the code point `ch` between indices [start, end) and
     * returns the index of the first occurrence or -1 when not found. Both
     * start and end are interpreted as given (negative values are not
     * adjusted by this helper).
     *
     * Implementations must perform bounds checking and return -1 if no
     * occurrence is present in the requested slice.
     */
    virtual Py_ssize_t findc(Py_ssize_t start, Py_ssize_t end, uint32_t ch) const = 0;

    /**
     * @brief Find a single code point in the buffer searching backward.
     *
     * Searches for the code point `ch` between indices [start, end) from
     * the right and returns the index of the last occurrence or -1 when
     * not found. Both start and end are interpreted as given (negative
     * values are not adjusted by this helper).
     */
    virtual Py_ssize_t rfindc(Py_ssize_t start, Py_ssize_t end, uint32_t ch) const = 0;

    /**
     * @brief Compute or return a cached hash value for this buffer.
     * @return Py_hash_t hash value.
     */
    Py_hash_t hash() {
        if (cached_hash != -1) {
            return cached_hash;
        }
        cached_hash = compute_hash();
        return cached_hash;
    }

    /**
     * @brief Lexicographic comparison between two buffers.
     *
     * Virtual method that allows derived classes to provide optimized
     * implementations. The default implementation performs character-by-
     * character comparison.
     *
     * @param other Other buffer to compare with.
     * @return -1 if *this < other, 0 if equal, 1 if *this > other.
     */
    virtual int cmp(const Buffer* other) const {
        Py_ssize_t len1 = length();
        Py_ssize_t len2 = other->length();
        Py_ssize_t minlen = (len1 < len2) ? len1 : len2;

        for (Py_ssize_t i = 0; i < minlen; ++i) {
            uint32_t c1 = value(i);
            uint32_t c2 = other->value(i);
            if (c1 < c2) return -1;
            if (c1 > c2) return 1;
        }
        if (len1 < len2) return -1;
        if (len1 > len2) return 1;
        return 0;
    }

private:
    /**
     * @brief Compute the hash value for the buffer contents.
     *
     * This computes a simple rolling hash over code points and returns a
     * Py_hash_t. The result is adjusted to avoid the reserved -1 value.
     * @return computed hash value (never -1).
     */
    Py_hash_t compute_hash() const {
        Py_ssize_t len = length();
        Py_hash_t x = 0;
        Py_hash_t mult = 31;  // multiplier
        for (Py_ssize_t i = 0; i < len; i++) {
            uint32_t ch = value(i);
            x = x * mult + ch;
        }
        if (x == -1) {
            x = -2;  // avoid reserved error value
        }
        return x;
    }
};

#endif // BUFFER_HXX
