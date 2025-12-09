#ifndef JOIN_BUFFER_HXX
#define JOIN_BUFFER_HXX

#include <Python.h>
#include <cstdint>

#include "buffer.hxx"
#include <cppy/ptr.h>

// ============================================================
// JoinBuffer — concatenation of two buffers
// ============================================================
class JoinBuffer : public Buffer {
private:
    cppy::ptr left_obj;
    cppy::ptr right_obj;

public:
    JoinBuffer(PyObject *left, PyObject *right)
        : left_obj(left, true), right_obj(right, true) {
    }

    ~JoinBuffer() override = default;

    Py_ssize_t length() const override {
        Buffer *lbuf = get_buffer(left_obj.get());
        Buffer *rbuf = get_buffer(right_obj.get());
        return lbuf->length() + rbuf->length();
    }

    int unicode_kind() const override {
        Buffer *lbuf = get_buffer(left_obj.get());
        Buffer *rbuf = get_buffer(right_obj.get());
        return std::max(lbuf->unicode_kind(), rbuf->unicode_kind());
    }

    uint32_t value(Py_ssize_t index) const override {
        Buffer *lbuf = get_buffer(left_obj.get());
        Py_ssize_t llen = lbuf->length();
        if (index < llen) {
            return lbuf->value(index);
        }
        Buffer *rbuf = get_buffer(right_obj.get());
        return rbuf->value(index - llen);
    }

    void copy(uint32_t *target, Py_ssize_t start, Py_ssize_t count) const override {
        Buffer *lbuf = get_buffer(left_obj.get());
        Buffer *rbuf = get_buffer(right_obj.get());
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
        Buffer *lbuf = get_buffer(left_obj.get());
        Buffer *rbuf = get_buffer(right_obj.get());
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
        Buffer *lbuf = get_buffer(left_obj.get());
        Buffer *rbuf = get_buffer(right_obj.get());
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
        Buffer *lbuf = get_buffer(left_obj.get());
        Buffer *rbuf = get_buffer(right_obj.get());

        cppy::ptr lrepr( lbuf->repr() );
        cppy::ptr rrepr( rbuf->repr() );
        if (!lrepr || !rrepr) return nullptr;
        PyObject *result = PyUnicode_FromFormat("(%U + %U)", lrepr.get(), rrepr.get());
        return result;
    }
};

#endif // JOIN_BUFFER_HXX
