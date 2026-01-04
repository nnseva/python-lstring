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

    /**
     * @brief Helper to check titlecase property for a range of characters.
     *
     * Checks if characters in range [0, check_len) satisfy titlecase rules:
     * uppercase/titlecase characters may only follow uncased characters,
     * lowercase characters may only follow cased characters.
     *
     * @param check_len Number of characters to check.
     * @return true if range is titlecased and has at least one cased character.
     */
    bool check_istitle_range(Py_ssize_t check_len) const {
        if (check_len == 0) return false;
        bool previous_is_cased = false;
        bool has_cased = false;
        
        for (Py_ssize_t i = 0; i < check_len; ++i) {
            Py_UCS4 ch = value(i);
            
            if (Py_UNICODE_ISUPPER(ch) || Py_UNICODE_ISTITLE(ch)) {
                if (previous_is_cased) {
                    return false;
                }
                previous_is_cased = true;
                has_cased = true;
            } else if (Py_UNICODE_ISLOWER(ch)) {
                if (!previous_is_cased) {
                    return false;
                }
                previous_is_cased = true;
                has_cased = true;
            } else {
                previous_is_cased = false;
            }
        }
        return has_cased;
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
     * @brief Find any character from a set in the buffer searching forward.
     *
     * Searches for any code point present in the charset buffer between
     * indices [start, end) and returns the index of the first occurrence
     * or -1 when not found. Both start and end are interpreted as given
     * (negative values are not adjusted by this helper).
     *
     * @param start Start index (inclusive)
     * @param end End index (exclusive)
     * @param charset Buffer containing the set of characters to search for
     * @param invert If true, find first character NOT in charset
     * @return Index of first matching character, or -1 if not found
     */
    virtual Py_ssize_t findcs(Py_ssize_t start, Py_ssize_t end, const Buffer* charset, bool invert = false) const {
        if (start < 0) start = 0;
        Py_ssize_t len = length();
        if (end > len) end = len;
        if (start >= end) return -1;
        if (!charset || charset->length() == 0) return invert ? (start < end ? start : -1) : -1;
        
        Py_ssize_t charset_len = charset->length();
        for (Py_ssize_t i = start; i < end; ++i) {
            uint32_t ch = value(i);
            bool found = false;
            for (Py_ssize_t j = 0; j < charset_len; ++j) {
                if (ch == charset->value(j)) {
                    found = true;
                    break;
                }
            }
            if (found != invert) {
                return i;
            }
        }
        return -1;
    }

    /**
     * @brief Find any character from a set in the buffer searching backward.
     *
     * Searches for any code point present in the charset buffer between
     * indices [start, end) from the right and returns the index of the
     * last occurrence or -1 when not found. Both start and end are
     * interpreted as given (negative values are not adjusted by this helper).
     *
     * @param start Start index (inclusive)
     * @param end End index (exclusive)
     * @param charset Buffer containing the set of characters to search for
     * @param invert If true, find last character NOT in charset
     * @return Index of last matching character, or -1 if not found
     */
    virtual Py_ssize_t rfindcs(Py_ssize_t start, Py_ssize_t end, const Buffer* charset, bool invert = false) const {
        if (start < 0) start = 0;
        Py_ssize_t len = length();
        if (end > len) end = len;
        if (start >= end) return -1;
        if (!charset || charset->length() == 0) return invert ? (end > start ? end - 1 : -1) : -1;
        
        Py_ssize_t charset_len = charset->length();
        for (Py_ssize_t i = end - 1; i >= start; --i) {
            uint32_t ch = value(i);
            bool found = false;
            for (Py_ssize_t j = 0; j < charset_len; ++j) {
                if (ch == charset->value(j)) {
                    found = true;
                    break;
                }
            }
            if (found != invert) {
                return i;
            }
        }
        return -1;
    }

    /**
     * @brief Find first character matching character class(es) searching forward.
     *
     * Searches for a character that matches the specified character class mask
     * between indices [start, end). Returns the index of the first matching
     * character or -1 when not found.
     *
     * @param start Start index (inclusive)
     * @param end End index (exclusive)
     * @param class_mask Character class flags (can be combined with bitwise OR)
     * @param invert If true, find first character NOT matching the class
     * @return Index of first matching character, or -1 if not found
     */
    virtual Py_ssize_t findcc(Py_ssize_t start, Py_ssize_t end, uint32_t class_mask, bool invert = false) const {
        if (start < 0) start = 0;
        Py_ssize_t len = length();
        if (end > len) end = len;
        if (start >= end) return -1;
        
        for (Py_ssize_t i = start; i < end; ++i) {
            bool matches = char_is(value(i), class_mask);
            if (matches != invert) {
                return i;
            }
        }
        return -1;
    }

    /**
     * @brief Find first character matching character class(es) searching backward.
     *
     * Searches for a character that matches the specified character class mask
     * between indices [start, end) from the right. Returns the index of the last
     * matching character or -1 when not found.
     *
     * @param start Start index (inclusive)
     * @param end End index (exclusive)
     * @param class_mask Character class flags (can be combined with bitwise OR)
     * @param invert If true, find last character NOT matching the class
     * @return Index of last matching character, or -1 if not found
     */
    virtual Py_ssize_t rfindcc(Py_ssize_t start, Py_ssize_t end, uint32_t class_mask, bool invert = false) const {
        if (start < 0) start = 0;
        Py_ssize_t len = length();
        if (end > len) end = len;
        if (start >= end) return -1;
        
        for (Py_ssize_t i = end - 1; i >= start; --i) {
            bool matches = char_is(value(i), class_mask);
            if (matches != invert) {
                return i;
            }
        }
        return -1;
    }

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

    /**
     * @brief Check if all characters in the buffer are whitespace.
     *
     * Returns true if all characters are whitespace according to
     * Py_UNICODE_ISSPACE, false otherwise. Returns false for empty buffers.
     *
     * @return true if all characters are whitespace, false otherwise.
     */
    virtual bool isspace() const {
        Py_ssize_t len = length();
        if (len == 0) return false;
        for (Py_ssize_t i = 0; i < len; ++i) {
            if (!Py_UNICODE_ISSPACE(value(i))) {
                return false;
            }
        }
        return true;
    }

    /**
     * @brief Check if all characters in the buffer are alphabetic.
     *
     * Returns true if all characters are alphabetic according to
     * Py_UNICODE_ISALPHA, false otherwise. Returns false for empty buffers.
     *
     * @return true if all characters are alphabetic, false otherwise.
     */
    virtual bool isalpha() const {
        Py_ssize_t len = length();
        if (len == 0) return false;
        for (Py_ssize_t i = 0; i < len; ++i) {
            if (!Py_UNICODE_ISALPHA(value(i))) {
                return false;
            }
        }
        return true;
    }

    /**
     * @brief Check if all characters in the buffer are digits.
     *
     * Returns true if all characters are digits according to
     * Py_UNICODE_ISDIGIT, false otherwise. Returns false for empty buffers.
     *
     * @return true if all characters are digits, false otherwise.
     */
    virtual bool isdigit() const {
        Py_ssize_t len = length();
        if (len == 0) return false;
        for (Py_ssize_t i = 0; i < len; ++i) {
            if (!Py_UNICODE_ISDIGIT(value(i))) {
                return false;
            }
        }
        return true;
    }

    /**
     * @brief Check if all characters in the buffer are alphanumeric.
     *
     * Returns true if all characters are alphanumeric according to
     * Py_UNICODE_ISALNUM, false otherwise. Returns false for empty buffers.
     *
     * @return true if all characters are alphanumeric, false otherwise.
     */
    virtual bool isalnum() const {
        Py_ssize_t len = length();
        if (len == 0) return false;
        for (Py_ssize_t i = 0; i < len; ++i) {
            if (!Py_UNICODE_ISALNUM(value(i))) {
                return false;
            }
        }
        return true;
    }

    /**
     * @brief Check if all characters in the buffer are uppercase.
     *
     * Returns true if all cased characters are uppercase according to
     * Py_UNICODE_ISUPPER and there is at least one cased character.
     * Returns false for empty buffers.
     *
     * @return true if all cased characters are uppercase, false otherwise.
     */
    virtual bool isupper() const {
        Py_ssize_t len = length();
        if (len == 0) return false;
        bool has_cased = false;
        for (Py_ssize_t i = 0; i < len; ++i) {
            Py_UCS4 ch = value(i);
            if (Py_UNICODE_ISLOWER(ch)) {
                return false;
            }
            if (Py_UNICODE_ISUPPER(ch)) {
                has_cased = true;
            }
        }
        return has_cased;
    }

    /**
     * @brief Check if all characters in the buffer are lowercase.
     *
     * Returns true if all cased characters are lowercase according to
     * Py_UNICODE_ISLOWER and there is at least one cased character.
     * Returns false for empty buffers.
     *
     * @return true if all cased characters are lowercase, false otherwise.
     */
    virtual bool islower() const {
        Py_ssize_t len = length();
        if (len == 0) return false;
        bool has_cased = false;
        for (Py_ssize_t i = 0; i < len; ++i) {
            Py_UCS4 ch = value(i);
            if (Py_UNICODE_ISUPPER(ch)) {
                return false;
            }
            if (Py_UNICODE_ISLOWER(ch)) {
                has_cased = true;
            }
        }
        return has_cased;
    }

    /**
     * @brief Check if all characters in the buffer are decimal digits.
     *
     * Returns true if all characters are decimal digits according to
     * Py_UNICODE_ISDECIMAL, false otherwise. Returns false for empty buffers.
     *
     * @return true if all characters are decimal digits, false otherwise.
     */
    virtual bool isdecimal() const {
        Py_ssize_t len = length();
        if (len == 0) return false;
        for (Py_ssize_t i = 0; i < len; ++i) {
            if (!Py_UNICODE_ISDECIMAL(value(i))) {
                return false;
            }
        }
        return true;
    }

    /**
     * @brief Check if all characters in the buffer are numeric.
     *
     * Returns true if all characters are numeric according to
     * Py_UNICODE_ISNUMERIC, false otherwise. Returns false for empty buffers.
     *
     * @return true if all characters are numeric, false otherwise.
     */
    virtual bool isnumeric() const {
        Py_ssize_t len = length();
        if (len == 0) return false;
        for (Py_ssize_t i = 0; i < len; ++i) {
            if (!Py_UNICODE_ISNUMERIC(value(i))) {
                return false;
            }
        }
        return true;
    }

    /**
     * @brief Check if all characters in the buffer are printable.
     *
     * Returns true if all characters are printable according to
     * Py_UNICODE_ISPRINTABLE, false otherwise. Returns true for empty buffers
     * (consistent with Python's str.isprintable()).
     *
     * @return true if all characters are printable or buffer is empty, false otherwise.
     */
    virtual bool isprintable() const {
        Py_ssize_t len = length();
        if (len == 0) return true;  // Empty string is considered printable
        for (Py_ssize_t i = 0; i < len; ++i) {
            if (!Py_UNICODE_ISPRINTABLE(value(i))) {
                return false;
            }
        }
        return true;
    }

    /**
     * @brief Check if the buffer is in titlecase.
     *
     * Returns true if the buffer is titlecased: uppercase characters may
     * only follow uncased characters and lowercase characters only cased ones.
     * Returns false for empty buffers.
     *
     * @return true if the buffer is titlecased, false otherwise.
     */
    virtual bool istitle() const {
        return check_istitle_range(length());
    }

    /**
     * @brief Collapse the buffer to a concrete string representation.
     *
     * This method is a no-op in the base Buffer class. Derived classes
     * may override to force materialization of lazy operations.
     *
     * @return New Buffer* if collapsed, nullptr if no change was made.
     */
    virtual Buffer* collapse() {
        // No-op in base class
        return nullptr;
    }

    /**
     * @brief Optimize the buffer if beneficial.
     *
     * Derived classes
     * may override it.
     *
     * @return New Buffer* if optimized, nullptr if no change was made.
     */
    virtual Buffer* optimize() {
        if (g_optimize_threshold <= 0) return nullptr;
        if ((Py_ssize_t)length() < g_optimize_threshold)
            return collapse();
        return nullptr;
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
