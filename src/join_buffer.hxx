#ifndef JOIN_BUFFER_HXX
#define JOIN_BUFFER_HXX

#include <Python.h>
#include <stdexcept>
#include <cstdint>
#include <string>

#include "buffer.hxx"

// ============================================================
// JoinBuffer — объединение двух буферов
// ============================================================
class JoinBuffer : public Buffer {
private:
    PyObject *left_obj;
    PyObject *right_obj;

public:
    JoinBuffer(PyObject *left, PyObject *right)
        : left_obj(left), right_obj(right) {
        Py_INCREF(left_obj);
        Py_INCREF(right_obj);
    }

    ~JoinBuffer() override {
        Py_XDECREF(left_obj);
        Py_XDECREF(right_obj);
    }

    Py_ssize_t length() const override {
        Buffer *lbuf = get_buffer(left_obj);
        Buffer *rbuf = get_buffer(right_obj);
        return lbuf->length() + rbuf->length();
    }

    int unicode_kind() const override {
        Buffer *lbuf = get_buffer(left_obj);
        Buffer *rbuf = get_buffer(right_obj);
        return std::max(lbuf->unicode_kind(), rbuf->unicode_kind());
    }

    uint32_t value(Py_ssize_t index) const override {
        Buffer *lbuf = get_buffer(left_obj);
        Py_ssize_t llen = lbuf->length();
        if (index < llen) {
            return lbuf->value(index);
        }
        Buffer *rbuf = get_buffer(right_obj);
        return rbuf->value(index - llen);
    }

    void copy(uint32_t *target, Py_ssize_t start, Py_ssize_t count) const override {
        Buffer *lbuf = get_buffer(left_obj);
        Buffer *rbuf = get_buffer(right_obj);
        Py_ssize_t llen = lbuf->length();

        if (start < llen) {
            Py_ssize_t left_count = std::min(count, llen - start);
            lbuf->copy(target, start, left_count);
            if (left_count < count) {
                rbuf->copy(target + left_count, 0, count - left_count);
            }
        } else {
            rbuf->copy(target, start - llen, count);
        }
    }

    void copy(uint16_t *target, Py_ssize_t start, Py_ssize_t count) const override {
        Buffer *lbuf = get_buffer(left_obj);
        Buffer *rbuf = get_buffer(right_obj);
        Py_ssize_t llen = lbuf->length();

        if (start < llen) {
            Py_ssize_t left_count = std::min(count, llen - start);
            lbuf->copy(target, start, left_count);
            if (left_count < count) {
                rbuf->copy(target + left_count, 0, count - left_count);
            }
        } else {
            rbuf->copy(target, start - llen, count);
        }
    }

    void copy(uint8_t *target, Py_ssize_t start, Py_ssize_t count) const override {
        Buffer *lbuf = get_buffer(left_obj);
        Buffer *rbuf = get_buffer(right_obj);
        Py_ssize_t llen = lbuf->length();

        if (start < llen) {
            Py_ssize_t left_count = std::min(count, llen - start);
            lbuf->copy(target, start, left_count);
            if (left_count < count) {
                rbuf->copy(target + left_count, 0, count - left_count);
            }
        } else {
            rbuf->copy(target, start - llen, count);
        }
    }

    // ---------- repr ----------
    PyObject* repr() const override {
        Buffer *lbuf = get_buffer(left_obj);
        Buffer *rbuf = get_buffer(right_obj);

        PyObject *lrepr = lbuf->repr();
        PyObject *rrepr = rbuf->repr();
        if (!lrepr || !rrepr) {
            Py_XDECREF(lrepr);
            Py_XDECREF(rrepr);
            return nullptr;
        }

        PyObject *result = PyUnicode_FromFormat("(%U + %U)", lrepr, rrepr);
        Py_DECREF(lrepr);
        Py_DECREF(rrepr);
        return result;
    }
};

#endif // JOIN_BUFFER_HXX
