#ifndef MUL_BUFFER_HXX
#define MUL_BUFFER_HXX

#include <Python.h>
#include <stdexcept>
#include <cstdint>

#include "lstring/lstring.hxx"
#include "str_buffer.hxx"
#include "tptr.hxx"
#include "lstring_utils.hxx"
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

    template <typename FindFn>
    Py_ssize_t find_2part(Py_ssize_t start, Py_ssize_t end, Py_ssize_t base_len, FindFn&& fn) const {
        Py_ssize_t rep_start = start / base_len;
        Py_ssize_t off_start = start - rep_start * base_len;
        Py_ssize_t block_end = (rep_start + 1) * base_len;

        if (end <= block_end) {
            Py_ssize_t off_end = off_start + (end - start);
            Py_ssize_t pos = fn(off_start, off_end);
            return (pos == -1) ? -1 : (rep_start * base_len + pos);
        }

        Py_ssize_t pos = fn(off_start, base_len);
        if (pos != -1) return rep_start * base_len + pos;

        Py_ssize_t rep_next = rep_start + 1;
        Py_ssize_t avail_next = end - rep_next * base_len;
        if (avail_next <= 0) return -1;
        Py_ssize_t limit = (avail_next < base_len) ? avail_next : base_len;
        if (limit == base_len) limit = off_start;
        if (limit <= 0) return -1;

        Py_ssize_t pos2 = fn(0, limit);
        return (pos2 == -1) ? -1 : (rep_next * base_len + pos2);
    }

    template <typename RFindFn>
    Py_ssize_t rfind_2part(Py_ssize_t start, Py_ssize_t end, Py_ssize_t base_len, RFindFn&& fn) const {
        Py_ssize_t last_index = end - 1;
        Py_ssize_t rep_last = last_index / base_len;
        Py_ssize_t off_end = (last_index - rep_last * base_len) + 1; // 1..base_len

        Py_ssize_t rep_start = start / base_len;
        Py_ssize_t off_start = start - rep_start * base_len;

        if (rep_last == rep_start) {
            Py_ssize_t pos = fn(off_start, off_end);
            return (pos == -1) ? -1 : (rep_last * base_len + pos);
        }

        Py_ssize_t pos = fn(0, off_end);
        if (pos != -1) return rep_last * base_len + pos;

        Py_ssize_t rep_prev = rep_last - 1;
        Py_ssize_t low = off_end;
        if (rep_prev == rep_start && low < off_start) low = off_start;
        if (low >= base_len) return -1;

        Py_ssize_t pos2 = fn(low, base_len);
        return (pos2 == -1) ? -1 : (rep_prev * base_len + pos2);
    }

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
        return PyUnicode_FromFormat("(%U * %zd)", lrepr.get(), repeat_count);
    }

    Py_ssize_t findc(Py_ssize_t start, Py_ssize_t end, uint32_t ch) const override {
        Py_ssize_t base_len = lstr_obj->buffer->length();
        if (base_len <= 0) return -1;

        // Basic safety: callers (e.g. LStr_findc) usually normalize start/end,
        // but keep this robust for internal calls.
        if (start < 0) start = 0;
        Py_ssize_t total_len = length();
        if (end > total_len) end = total_len;
        if (start >= end) return -1;

        auto fn = [&](Py_ssize_t s, Py_ssize_t e) -> Py_ssize_t {
            return lstr_obj->buffer->findc(s, e, ch);
        };
        return find_2part(start, end, base_len, fn);
    }

    Py_ssize_t rfindc(Py_ssize_t start, Py_ssize_t end, uint32_t ch) const override {
        Py_ssize_t base_len = lstr_obj->buffer->length();
        if (base_len <= 0) return -1;

        // Basic safety normalization.
        if (start < 0) start = 0;
        Py_ssize_t total_len = length();
        if (end > total_len) end = total_len;
        if (start >= end) return -1;

        auto fn = [&](Py_ssize_t s, Py_ssize_t e) -> Py_ssize_t {
            return lstr_obj->buffer->rfindc(s, e, ch);
        };
        return rfind_2part(start, end, base_len, fn);
    }

    /**
     * @brief Find first character in charset.
     *
     * Optimized for MulBuffer: since the base string repeats with period base_len,
     * if a match exists within [start,end) then it will be found within the first
     * base_len characters from start. Limit search range and delegate to base class.
     */
    Py_ssize_t findcs(Py_ssize_t start, Py_ssize_t end, const CharSet& charset, bool invert = false) const override {
        Py_ssize_t base_len = lstr_obj->buffer->length();
        if (base_len <= 0) return -1;

        if (start < 0) start = 0;
        Py_ssize_t total_len = length();
        if (end > total_len) end = total_len;
        if (start >= end) return -1;

        auto fn = [&](Py_ssize_t s, Py_ssize_t e) -> Py_ssize_t {
            return lstr_obj->buffer->findcs(s, e, charset, invert);
        };
        return find_2part(start, end, base_len, fn);
    }

    /**
     * @brief Find last character in charset.
     *
     * Optimized for MulBuffer: since the base string repeats with period base_len,
     * if a match exists within [start,end) then it will be found within the last
     * base_len characters ending at end. Limit search range and delegate to base class.
     */
    Py_ssize_t rfindcs(Py_ssize_t start, Py_ssize_t end, const CharSet& charset, bool invert = false) const override {
        Py_ssize_t base_len = lstr_obj->buffer->length();
        if (base_len <= 0) return -1;

        if (start < 0) start = 0;
        Py_ssize_t total_len = length();
        if (end > total_len) end = total_len;
        if (start >= end) return -1;

        auto fn = [&](Py_ssize_t s, Py_ssize_t e) -> Py_ssize_t {
            return lstr_obj->buffer->rfindcs(s, e, charset, invert);
        };
        return rfind_2part(start, end, base_len, fn);
    }

    /**
     * @brief Find first character in code point range [startcp, endcp).
     * 
     * Optimized for MulBuffer: since the base string repeats, if a character
     * exists anywhere in the repeated string, it will be found within the first
     * base_len characters. Limit search range and delegate to base class.
     */
    Py_ssize_t findcr(Py_ssize_t start, Py_ssize_t end, uint32_t startcp, uint32_t endcp, bool invert) const override {
        Py_ssize_t base_len = lstr_obj->buffer->length();
        if (base_len <= 0) return -1;

        if (start < 0) start = 0;
        Py_ssize_t total_len = length();
        if (end > total_len) end = total_len;
        if (start >= end) return -1;

        auto fn = [&](Py_ssize_t s, Py_ssize_t e) -> Py_ssize_t {
            return lstr_obj->buffer->findcr(s, e, startcp, endcp, invert);
        };
        return find_2part(start, end, base_len, fn);
    }

    /**
     * @brief Find last character in code point range [startcp, endcp).
     * 
     * Optimized for MulBuffer: since the base string repeats, if a character
     * exists anywhere in the repeated string, it will be found within the last
     * base_len characters. Limit search range and delegate to base class.
     */
    Py_ssize_t rfindcr(Py_ssize_t start, Py_ssize_t end, uint32_t startcp, uint32_t endcp, bool invert) const override {
        Py_ssize_t base_len = lstr_obj->buffer->length();
        if (base_len <= 0) return -1;

        if (start < 0) start = 0;
        Py_ssize_t total_len = length();
        if (end > total_len) end = total_len;
        if (start >= end) return -1;

        auto fn = [&](Py_ssize_t s, Py_ssize_t e) -> Py_ssize_t {
            return lstr_obj->buffer->rfindcr(s, e, startcp, endcp, invert);
        };
        return rfind_2part(start, end, base_len, fn);
    }

    /**
     * @brief Find first character that matches a character class mask.
     *
     * Optimized for MulBuffer: since the base string repeats with period base_len,
     * if a match exists within [start,end) then it will be found within the first
     * base_len characters from start. Limit search range and delegate to base class.
     */
    Py_ssize_t findcc(Py_ssize_t start, Py_ssize_t end, uint32_t class_mask, bool invert = false) const override {
        Py_ssize_t base_len = lstr_obj->buffer->length();
        if (base_len <= 0) return -1;

        if (start < 0) start = 0;
        Py_ssize_t total_len = length();
        if (end > total_len) end = total_len;
        if (start >= end) return -1;

        auto fn = [&](Py_ssize_t s, Py_ssize_t e) -> Py_ssize_t {
            return lstr_obj->buffer->findcc(s, e, class_mask, invert);
        };
        return find_2part(start, end, base_len, fn);
    }

    /**
     * @brief Find last character that matches a character class mask.
     *
     * Optimized for MulBuffer: since the base string repeats with period base_len,
     * if a match exists within [start,end) then it will be found within the last
     * base_len characters ending at end. Limit search range and delegate to base class.
     */
    Py_ssize_t rfindcc(Py_ssize_t start, Py_ssize_t end, uint32_t class_mask, bool invert = false) const override {
        Py_ssize_t base_len = lstr_obj->buffer->length();
        if (base_len <= 0) return -1;

        if (start < 0) start = 0;
        Py_ssize_t total_len = length();
        if (end > total_len) end = total_len;
        if (start >= end) return -1;

        auto fn = [&](Py_ssize_t s, Py_ssize_t e) -> Py_ssize_t {
            return lstr_obj->buffer->rfindcc(s, e, class_mask, invert);
        };
        return rfind_2part(start, end, base_len, fn);
    }

    /**
     * @brief Character classification methods with delegation to base buffer.
     *
     * If a property holds for all characters in the base string, it holds
     * for all characters in all repetitions. We delegate to the base buffer.
     * 
     * Note: istitle() is not delegated as it depends on character positions
     * and can fail at repetition boundaries.
     */
    bool isspace() const override {
        if (repeat_count == 0) return false;
        return lstr_obj->buffer->isspace();
    }

    bool isalpha() const override {
        if (repeat_count == 0) return false;
        return lstr_obj->buffer->isalpha();
    }

    bool isdigit() const override {
        if (repeat_count == 0) return false;
        return lstr_obj->buffer->isdigit();
    }

    bool isalnum() const override {
        if (repeat_count == 0) return false;
        return lstr_obj->buffer->isalnum();
    }

    bool isupper() const override {
        if (repeat_count == 0) return false;
        return lstr_obj->buffer->isupper();
    }

    bool islower() const override {
        if (repeat_count == 0) return false;
        return lstr_obj->buffer->islower();
    }

    bool isdecimal() const override {
        if (repeat_count == 0) return false;
        return lstr_obj->buffer->isdecimal();
    }

    bool isnumeric() const override {
        if (repeat_count == 0) return false;
        return lstr_obj->buffer->isnumeric();
    }

    bool isprintable() const override {
        if (repeat_count == 0) return true;  // Empty string is printable
        return lstr_obj->buffer->isprintable();
    }

    bool istitle() const override {
        if (repeat_count == 0) return false;
        if (repeat_count == 1) return lstr_obj->buffer->istitle();
        
        // For repeat_count >= 2, check first two repetitions (includes boundary)
        Py_ssize_t base_len = lstr_obj->buffer->length();
        if (base_len == 0) return false;
        
        return check_istitle_range(2 * base_len);
    }
};

#endif // MUL_BUFFER_HXX
