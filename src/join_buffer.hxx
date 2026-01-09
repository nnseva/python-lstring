#ifndef JOIN_BUFFER_HXX
#define JOIN_BUFFER_HXX

#include <Python.h>
#include <cstdint>

#include "lstring/lstring.hxx"
#include "str_buffer.hxx"
#include "tptr.hxx"
#include "lstring_utils.hxx"
#include <cppy/ptr.h>

/**
 * @brief JoinBuffer — concatenation of two buffers
 *
 * Implements a lazy concatenation view over two Buffer instances.
 */
class JoinBuffer : public Buffer {
private:
    tptr<LStrObject> left_obj;
    tptr<LStrObject> right_obj;

public:
    /**
     * @brief Construct a lazy concatenation buffer.
     *
     * The JoinBuffer holds references to the two Python objects (which
     * are expected to provide Buffer implementations) and presents a
     * concatenated view over them.
     *
     * @param left Left operand (borrowed reference)
     * @param right Right operand (borrowed reference)
     */
    JoinBuffer(PyObject *left, PyObject *right)
        : left_obj(left, true), right_obj(right, true) {
    }

    /**
     * @brief Destructor.
     *
     * Defaulted; held cppy::ptr members will release their references.
     */
    ~JoinBuffer() override = default;

    /**
     * @brief Total length (number of code points) of the concatenated view.
     *
     * @return Sum of left->length() and right->length().
     */
    Py_ssize_t length() const override {
        return left_obj->buffer->length() + right_obj->buffer->length();
    }

    /**
     * @brief Unicode storage kind required to represent the concatenation.
     *
     * Returns the maximum unicode kind required by either side (1/2/4-byte).
     */
    int unicode_kind() const override {
        return std::max(left_obj->buffer->unicode_kind(), right_obj->buffer->unicode_kind());
    }

    /**
     * @brief Get the code point value at the given index in the concatenated view.
     *
     * @param index Index into the concatenated buffer (0-based).
     * @return Unicode code point value.
     */
    uint32_t value(Py_ssize_t index) const override {
        Py_ssize_t llen = left_obj->buffer->length();
        if (index < llen) {
            return left_obj->buffer->value(index);
        }
        return right_obj->buffer->value(index - llen);
    }

    /**
     * @brief Copy a range of code points into a 32-bit target buffer.
     *
     * Copies `count` code points starting at `start` into `target`.
     * The implementation splits the copy between left and right buffers
     * as needed.
     *
     * @param target Destination buffer of uint32_t elements.
     * @param start Start index in the concatenated view.
     * @param count Number of code points to copy.
     */
    void copy(uint32_t *target, Py_ssize_t start, Py_ssize_t count) const override {
        Py_ssize_t llen = left_obj->buffer->length();

        if (start < llen) {
            Py_ssize_t left_count = std::min(count, llen - start);
            left_obj->buffer->copy(target, start, left_count);
            if (left_count < count) {
                right_obj->buffer->copy(target + left_count, 0, count - left_count);
            }
        } else {
            right_obj->buffer->copy(target, start - llen, count);
        }
    }

    /**
     * @brief Copy a range of code points into a 16-bit target buffer.
     *
     * Same semantics as the uint32_t copy overload but copies into
     * a UTF-16 buffer.
     */
    void copy(uint16_t *target, Py_ssize_t start, Py_ssize_t count) const override {
        Py_ssize_t llen = left_obj->buffer->length();

        if (start < llen) {
            Py_ssize_t left_count = std::min(count, llen - start);
            left_obj->buffer->copy(target, start, left_count);
            if (left_count < count) {
                right_obj->buffer->copy(target + left_count, 0, count - left_count);
            }
        } else {
            right_obj->buffer->copy(target, start - llen, count);
        }
    }

    /**
     * @brief Copy a range of code points into an 8-bit target buffer.
     *
     * Same semantics as other copy overloads; used when both sides fit
     * into 1-byte storage.
     */
    void copy(uint8_t *target, Py_ssize_t start, Py_ssize_t count) const override {
        Py_ssize_t llen = left_obj->buffer->length();

        if (start < llen) {
            Py_ssize_t left_count = std::min(count, llen - start);
            left_obj->buffer->copy(target, start, left_count);
            if (left_count < count) {
                right_obj->buffer->copy(target + left_count, 0, count - left_count);
            }
        } else {
            right_obj->buffer->copy(target, start - llen, count);
        }
    }

    /**
     * @brief Produce a Python-level repr for the concatenation.
     *
     * The returned object is a new Python string describing the concatenation
     * in the form "(<left_repr> + <right_repr>)".
     */
    PyObject* repr() const override {
        tptr<LStrObject> lrepr( left_obj->buffer->repr() );
        tptr<LStrObject> rrepr( right_obj->buffer->repr() );
        if (!lrepr || !rrepr) return nullptr;
        return PyUnicode_FromFormat("(%U + %U)", lrepr.ptr().get(), rrepr.ptr().get());
    }

    /*
     * Implement single-character search for concatenated view.
     * Both start and end are interpreted as given; clamp to valid range
     * for this buffer implementation.
     */
    Py_ssize_t findc(Py_ssize_t start, Py_ssize_t end, uint32_t ch) const override {
        Py_ssize_t llen = left_obj->buffer->length();
        Py_ssize_t rlen = right_obj->buffer->length();
        Py_ssize_t total = llen + rlen;

        if (total <= 0) return -1;
        if (start < 0) start = 0;
        if (end < 0) end = 0;
        if (start > total) return -1;
        if (end > total) end = total;
        if (start >= end) return -1;

        // Search left portion
        if (start < llen) {
            Py_ssize_t left_start = start;
            Py_ssize_t left_end = (end < llen) ? end : llen;
            Py_ssize_t pos = left_obj->buffer->findc(left_start, left_end, ch);
            if (pos != -1) return pos;
        }

        // Search right portion
        if (end > llen) {
            Py_ssize_t right_start = (start > llen) ? (start - llen) : 0;
            Py_ssize_t right_end = end - llen;
            Py_ssize_t pos = right_obj->buffer->findc(right_start, right_end, ch);
            if (pos != -1) return pos + llen;
        }

        return -1;
    }

    Py_ssize_t rfindc(Py_ssize_t start, Py_ssize_t end, uint32_t ch) const override {
        Py_ssize_t llen = left_obj->buffer->length();
        Py_ssize_t rlen = right_obj->buffer->length();
        Py_ssize_t total = llen + rlen;

        if (total <= 0) return -1;
        if (start < 0) start = 0;
        if (end < 0) end = 0;
        if (start > total) return -1;
        if (end > total) end = total;
        if (start >= end) return -1;

        // Search right portion first
        if (end > llen) {
            Py_ssize_t right_start = (start > llen) ? (start - llen) : 0;
            Py_ssize_t right_end = end - llen;
            Py_ssize_t pos = right_obj->buffer->rfindc(right_start, right_end, ch);
            if (pos != -1) return pos + llen;
        }

        // Then search left portion
        if (start < llen) {
            Py_ssize_t left_start = start;
            Py_ssize_t left_end = (end < llen) ? end : llen;
            Py_ssize_t pos = left_obj->buffer->rfindc(left_start, left_end, ch);
            if (pos != -1) return pos;
        }

        return -1;
    }

    /**
     * @brief Character classification methods with delegation to left/right buffers.
     *
     * For non-context-dependent methods (isspace, isalpha, isdigit, isalnum,
     * isdecimal, isnumeric, isprintable), we can simply check that both
     * left and right buffers satisfy the condition.
     *
     * Context-dependent methods (isupper, islower, istitle) rely on the
     * base class implementation as they require positional information.
     */
    bool isspace() const override {
        return left_obj->buffer->isspace() && right_obj->buffer->isspace();
    }

    bool isalpha() const override {
        return left_obj->buffer->isalpha() && right_obj->buffer->isalpha();
    }

    bool isdigit() const override {
        return left_obj->buffer->isdigit() && right_obj->buffer->isdigit();
    }

    bool isalnum() const override {
        return left_obj->buffer->isalnum() && right_obj->buffer->isalnum();
    }

    bool isdecimal() const override {
        return left_obj->buffer->isdecimal() && right_obj->buffer->isdecimal();
    }

    bool isnumeric() const override {
        return left_obj->buffer->isnumeric() && right_obj->buffer->isnumeric();
    }

    bool isprintable() const override {
        return left_obj->buffer->isprintable() && right_obj->buffer->isprintable();
    }

    /**
     * @brief Unconditionally collapse this join into a concrete StrBuffer.
     *
     * Materializes the concatenation into a Python str object, then wraps it
     * in a StrBuffer. This is always performed regardless of threshold.
     *
     * @return New StrBuffer* on success, or nullptr on error.
     */
    Buffer* collapse() override {
        // First convert this buffer to a Python str
        cppy::ptr py_str(buffer_to_pystr(this));
        if (!py_str) return nullptr;

        // Then create a StrBuffer from it
        return make_str_buffer(py_str.get());
    }

    /**
     * @brief Optimize the buffer, recursively optimizing child buffers.
     *
     * First tries the base class optimization (threshold-based collapse).
     * If that doesn't apply, recursively optimizes left and right children.
     *
     * @return New Buffer* if optimized, nullptr if no change was made.
     */
    Buffer* optimize() override {
        // Try base class optimization first (threshold-based collapse)
        Buffer* new_buf = Buffer::optimize();
        if (new_buf) return new_buf;

        // Recursively optimize children
        lstr_optimize(left_obj.get());
        lstr_optimize(right_obj.get());
        
        return nullptr;
    }
};

#endif // JOIN_BUFFER_HXX
