/**
 * @file lstring.hxx
 * @brief Declarations for the L object and forward declarations.
 */

#ifndef LSTRING_HXX
#define LSTRING_HXX

#include <Python.h>
#include <cstdint>
#include <cstring>
#include <stdexcept>

/**
 * @brief Character class flags for efficient character classification
 * 
 * These flags can be combined with bitwise OR to check multiple classes.
 * Note: CHAR_ALNUM is a composite flag (ALPHA | NUMERIC) per Unicode standard.
 */
enum CharClass : uint32_t {
    CHAR_SPACE      = 1 << 0,   // Whitespace characters
    CHAR_ALPHA      = 1 << 1,   // Alphabetic characters
    CHAR_DIGIT      = 1 << 2,   // Digit characters
    CHAR_LOWER      = 1 << 3,   // Lowercase characters
    CHAR_UPPER      = 1 << 4,   // Uppercase characters
    CHAR_DECIMAL    = 1 << 5,   // Decimal digit characters
    CHAR_NUMERIC    = 1 << 6,   // Numeric characters (including fractions, Roman numerals)
    CHAR_PRINTABLE  = 1 << 7,   // Printable characters
    
    // Composite flags
    CHAR_ALNUM      = CHAR_ALPHA | CHAR_NUMERIC,  // Alphanumeric (alpha OR numeric)
};

/**
 * @brief Check if a character belongs to specified character class(es)
 * 
 * @param ch Unicode code point to check
 * @param charclass Character class flags (can be combined with bitwise OR)
 * @return true if character matches any of the specified classes
 */
inline bool char_is(uint32_t ch, uint32_t charclass) {
    return ((charclass & CHAR_SPACE) && Py_UNICODE_ISSPACE(ch)) ||
           ((charclass & CHAR_ALPHA) && Py_UNICODE_ISALPHA(ch)) ||
           ((charclass & CHAR_DIGIT) && Py_UNICODE_ISDIGIT(ch)) ||
           ((charclass & CHAR_LOWER) && Py_UNICODE_ISLOWER(ch)) ||
           ((charclass & CHAR_UPPER) && Py_UNICODE_ISUPPER(ch)) ||
           ((charclass & CHAR_DECIMAL) && Py_UNICODE_ISDECIMAL(ch)) ||
           ((charclass & CHAR_NUMERIC) && Py_UNICODE_ISNUMERIC(ch)) ||
           ((charclass & CHAR_PRINTABLE) && Py_UNICODE_ISPRINTABLE(ch));
}

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
    virtual ~Buffer();

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
    virtual bool is_str() const;

    /**
     * @brief Find a single code point in the buffer searching forward.
     */
    virtual Py_ssize_t findc(Py_ssize_t start, Py_ssize_t end, uint32_t ch) const = 0;

    /**
     * @brief Find a single code point in the buffer searching backward.
     */
    virtual Py_ssize_t rfindc(Py_ssize_t start, Py_ssize_t end, uint32_t ch) const = 0;

    /**
     * @brief Find any character from a set in the buffer searching forward.
     */
    virtual Py_ssize_t findcs(Py_ssize_t start, Py_ssize_t end, const Buffer* charset, bool invert = false) const;

    /**
     * @brief Find any character from a set in the buffer searching backward.
     */
    virtual Py_ssize_t rfindcs(Py_ssize_t start, Py_ssize_t end, const Buffer* charset, bool invert = false) const;

    /**
     * @brief Find any character in code point range searching forward.
     */
    virtual Py_ssize_t findcr(Py_ssize_t start, Py_ssize_t end, uint32_t startcp, uint32_t endcp, bool invert = false) const;

    /**
     * @brief Find any character in code point range searching backward.
     */
    virtual Py_ssize_t rfindcr(Py_ssize_t start, Py_ssize_t end, uint32_t startcp, uint32_t endcp, bool invert = false) const;

    /**
     * @brief Find first character matching character class(es) searching forward.
     */
    virtual Py_ssize_t findcc(Py_ssize_t start, Py_ssize_t end, uint32_t class_mask, bool invert = false) const;

    /**
     * @brief Find first character matching character class(es) searching backward.
     */
    virtual Py_ssize_t rfindcc(Py_ssize_t start, Py_ssize_t end, uint32_t class_mask, bool invert = false) const;

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
     */
    virtual int cmp(const Buffer* other) const;

    /**
     * @brief Check if all characters in the buffer are whitespace.
     */
    virtual bool isspace() const;

    /**
     * @brief Check if all characters in the buffer are alphabetic.
     */
    virtual bool isalpha() const;

    /**
     * @brief Check if all characters in the buffer are digits.
     */
    virtual bool isdigit() const;

    /**
     * @brief Check if all characters in the buffer are alphanumeric.
     */
    virtual bool isalnum() const;

    /**
     * @brief Check if all characters in the buffer are uppercase.
     */
    virtual bool isupper() const;

    /**
     * @brief Check if all characters in the buffer are lowercase.
     */
    virtual bool islower() const;

    /**
     * @brief Check if all characters in the buffer are decimal digits.
     */
    virtual bool isdecimal() const;

    /**
     * @brief Check if all characters in the buffer are numeric.
     */
    virtual bool isnumeric() const;

    /**
     * @brief Check if all characters in the buffer are printable.
     */
    virtual bool isprintable() const;

    /**
     * @brief Check if the buffer is in titlecase.
     */
    virtual bool istitle() const;

    /**
     * @brief Collapse the buffer to a concrete string representation.
     */
    virtual Buffer* collapse();

    /**
     * @brief Optimize the buffer if beneficial.
     */
    virtual Buffer* optimize();

private:
    /**
     * @brief Compute the hash value for the buffer contents.
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

/**
 * @struct LStrObject
 * @brief C struct backing the Python `L` type.
 *
 * Instances of this struct are the low-level CPython object used to
 * implement the `L` type. The `buffer` member points to a Buffer
 * implementation that lazily represents the string contents.
 */
struct LStrObject {
    PyObject_HEAD
    Buffer *buffer; /**< Pointer to the lazily-evaluated buffer */
};

#endif // LSTRING_HXX
