#ifndef BUFFER_HXX
#define BUFFER_HXX

#include <Python.h>
#include <stdexcept>
#include <cstdint>

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
public:
    virtual ~Buffer() {}

    virtual Py_ssize_t length() const = 0;
    virtual int unicode_kind() const = 0;
    virtual uint32_t value(Py_ssize_t index) const = 0;

    virtual void copy(uint32_t *target, Py_ssize_t start, Py_ssize_t count) const = 0;
    virtual void copy(uint16_t *target, Py_ssize_t start, Py_ssize_t count) const = 0;
    virtual void copy(uint8_t *target, Py_ssize_t start, Py_ssize_t count) const = 0;

    // Новый абстрактный метод для отладочного представления
    virtual PyObject* repr() const = 0;
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
        for (Py_ssize_t i = 0; i < count; ++i) {
            target[i] = static_cast<uint8_t>(PyUnicode_READ_CHAR(py_str, start + i));
        }
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
        for (Py_ssize_t i = 0; i < count; ++i) {
            target[i] = static_cast<uint8_t>(PyUnicode_READ_CHAR(py_str, start + i));
        }
    }

    PyObject* repr() const override {
        return PyObject_Repr(py_str);
    }
};

#endif // BUFFER_HXX
