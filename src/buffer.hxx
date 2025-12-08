#ifndef BUFFER_HXX
#define BUFFER_HXX

#include <Python.h>
#include <stdexcept>
#include <cstdint>
#include <cstring>

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

// ============================================================
// Str8Buffer
// ============================================================
class Str8Buffer : public Buffer {
private:
    PyObject *py_str;

public:
    Str8Buffer(PyObject *str) : py_str(str) {
        Py_INCREF(py_str);
    }
    ~Str8Buffer() override {
        Py_XDECREF(py_str);
    }

    Py_ssize_t length() const override {
        return PyUnicode_GET_LENGTH(py_str);
    }

    int unicode_kind() const override {
        return PyUnicode_1BYTE_KIND;
    }

    uint32_t value(Py_ssize_t index) const override {
        if (index < 0 || index >= length()) throw std::out_of_range("Str8Buffer: index out of range");
        return PyUnicode_READ_CHAR(py_str, index);
    }

    void copy(uint32_t *target, Py_ssize_t start, Py_ssize_t count) const override {
        for (Py_ssize_t i = 0; i < count; ++i) {
            target[i] = PyUnicode_READ_CHAR(py_str, start + i);
        }
    }
    void copy(uint16_t *target, Py_ssize_t start, Py_ssize_t count) const override {
        for (Py_ssize_t i = 0; i < count; ++i) {
            target[i] = static_cast<uint16_t>(PyUnicode_READ_CHAR(py_str, start + i));
        }
    }
    void copy(uint8_t *target, Py_ssize_t start, Py_ssize_t count) const override {
        const uint8_t *src = as_ucs1(py_str) + start;
        std::memcpy(target, src, count * sizeof(uint8_t));
    }

    PyObject* repr() const override {
        return PyObject_Repr(py_str);
    }
};

// ============================================================
// Str16Buffer
// ============================================================
class Str16Buffer : public Buffer {
private:
    PyObject *py_str;

public:
    Str16Buffer(PyObject *str) : py_str(str) {
        Py_INCREF(py_str);
    }
    ~Str16Buffer() override {
        Py_XDECREF(py_str);
    }

    Py_ssize_t length() const override {
        return PyUnicode_GET_LENGTH(py_str);
    }

    int unicode_kind() const override {
        return PyUnicode_2BYTE_KIND;
    }

    uint32_t value(Py_ssize_t index) const override {
        if (index < 0 || index >= length()) throw std::out_of_range("Str16Buffer: index out of range");
        return PyUnicode_READ_CHAR(py_str, index);
    }

    void copy(uint32_t *target, Py_ssize_t start, Py_ssize_t count) const override {
        for (Py_ssize_t i = 0; i < count; ++i) {
            target[i] = PyUnicode_READ_CHAR(py_str, start + i);
        }
    }
    void copy(uint16_t *target, Py_ssize_t start, Py_ssize_t count) const override {
        const uint16_t *src = as_ucs2(py_str) + start;
        std::memcpy(target, src, count * sizeof(uint16_t));
    }
    void copy(uint8_t *target, Py_ssize_t start, Py_ssize_t count) const override {
        for (Py_ssize_t i = 0; i < count; ++i) {
            target[i] = static_cast<uint8_t>(PyUnicode_READ_CHAR(py_str, start + i));
        }
    }

    PyObject* repr() const override {
        return PyObject_Repr(py_str);
    }
};

// ============================================================
// Str32Buffer
// ============================================================
class Str32Buffer : public Buffer {
private:
    PyObject *py_str;

public:
    Str32Buffer(PyObject *str) : py_str(str) {
        Py_INCREF(py_str);
    }
    ~Str32Buffer() override {
        Py_XDECREF(py_str);
    }

    Py_ssize_t length() const override {
        return PyUnicode_GET_LENGTH(py_str);
    }

    int unicode_kind() const override {
        return PyUnicode_4BYTE_KIND;
    }

    uint32_t value(Py_ssize_t index) const override {
        if (index < 0 || index >= length()) throw std::out_of_range("Str32Buffer: index out of range");
        return PyUnicode_READ_CHAR(py_str, index);
    }

    void copy(uint32_t *target, Py_ssize_t start, Py_ssize_t count) const override {
        const uint32_t *src = as_ucs4(py_str) + start;
        std::memcpy(target, src, count * sizeof(uint32_t));
    }
    void copy(uint16_t *target, Py_ssize_t start, Py_ssize_t count) const override {
        for (Py_ssize_t i = 0; i < count; ++i) {
            target[i] = static_cast<uint16_t>(PyUnicode_READ_CHAR(py_str, start + i));
        }
    }
    void copy(uint8_t *target, Py_ssize_t start, Py_ssize_t count) const override {
        for (Py_ssize_t i = 0; i < count; ++i) {
            target[i] = static_cast<uint8_t>(PyUnicode_READ_CHAR(py_str, start + i));
        }
    }

    PyObject* repr() const override {
        return PyObject_Repr(py_str);
    }
};

#endif // BUFFER_HXX
