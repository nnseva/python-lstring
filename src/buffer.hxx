#ifndef BUFFER_HXX
#define BUFFER_HXX

#include <Python.h>
#include <stdexcept>
#include <cstdint>
#include <cstring>

#include "lstring.hxx"

// ============================================================
// Abstract Buffer
// ============================================================
class Buffer {
protected:
    // Helper to get Buffer* from LStrObject
    static Buffer* get_buffer(PyObject *obj) {
        LStrObject *lstr = reinterpret_cast<LStrObject*>(obj);
        return lstr->buffer;
    }

    // Inline helpers to cast PyUnicode_DATA to proper type
    inline const uint8_t* as_ucs1(PyObject* s) const {
        return reinterpret_cast<const uint8_t*>(PyUnicode_DATA(s));
    }
    inline const uint16_t* as_ucs2(PyObject* s) const {
        return reinterpret_cast<const uint16_t*>(PyUnicode_DATA(s));
    }
    inline const uint32_t* as_ucs4(PyObject* s) const {
        return reinterpret_cast<const uint32_t*>(PyUnicode_DATA(s));
    }

    Py_hash_t cached_hash;  // cache for computed hash

public:
    Buffer() : cached_hash(-1) {}
    virtual ~Buffer() {}

    virtual Py_ssize_t length() const = 0;
    virtual int unicode_kind() const = 0;
    virtual uint32_t value(Py_ssize_t index) const = 0;

    virtual void copy(uint32_t *target, Py_ssize_t start, Py_ssize_t count) const = 0;
    virtual void copy(uint16_t *target, Py_ssize_t start, Py_ssize_t count) const = 0;
    virtual void copy(uint8_t *target, Py_ssize_t start, Py_ssize_t count) const = 0;

    virtual PyObject* repr() const = 0;

    // Check if the buffer is a string buffer (StrBuffer)
    virtual bool is_str() const {
        return false;
    }
    // non-const hash with caching
    Py_hash_t hash() {
        if (cached_hash != -1) {
            return cached_hash;
        }
        cached_hash = compute_hash();
        return cached_hash;
    }

    // alfanumeric comparison
    int cmp(const Buffer* other) const {
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
