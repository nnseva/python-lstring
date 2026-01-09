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

    inline const uint8_t* as_ucs1(PyObject* s) const {
        return reinterpret_cast<const uint8_t*>(PyUnicode_DATA(s));
    }
    inline const uint16_t* as_ucs2(PyObject* s) const {
        return reinterpret_cast<const uint16_t*>(PyUnicode_DATA(s));
    }
    inline const uint32_t* as_ucs4(PyObject* s) const {
        return reinterpret_cast<const uint32_t*>(PyUnicode_DATA(s));
    }

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

    Py_hash_t cached_hash;

public:
    Buffer() : cached_hash(-1) {}
    virtual ~Buffer();

    virtual Py_ssize_t length() const = 0;
    virtual int unicode_kind() const = 0;
    virtual uint32_t value(Py_ssize_t index) const = 0;

    virtual void copy(uint32_t *target, Py_ssize_t start, Py_ssize_t count) const = 0;
    virtual void copy(uint16_t *target, Py_ssize_t start, Py_ssize_t count) const = 0;
    virtual void copy(uint8_t *target, Py_ssize_t start, Py_ssize_t count) const = 0;

    virtual PyObject* repr() const = 0;

    virtual bool is_str() const;

    virtual Py_ssize_t findc(Py_ssize_t start, Py_ssize_t end, uint32_t ch) const = 0;
    virtual Py_ssize_t rfindc(Py_ssize_t start, Py_ssize_t end, uint32_t ch) const = 0;
    virtual Py_ssize_t findcs(Py_ssize_t start, Py_ssize_t end, const Buffer* charset, bool invert = false) const;
    virtual Py_ssize_t rfindcs(Py_ssize_t start, Py_ssize_t end, const Buffer* charset, bool invert = false) const;
    virtual Py_ssize_t findcr(Py_ssize_t start, Py_ssize_t end, uint32_t startcp, uint32_t endcp, bool invert = false) const;
    virtual Py_ssize_t rfindcr(Py_ssize_t start, Py_ssize_t end, uint32_t startcp, uint32_t endcp, bool invert = false) const;
    virtual Py_ssize_t findcc(Py_ssize_t start, Py_ssize_t end, uint32_t class_mask, bool invert = false) const;
    virtual Py_ssize_t rfindcc(Py_ssize_t start, Py_ssize_t end, uint32_t class_mask, bool invert = false) const;

    Py_hash_t hash() {
        if (cached_hash != -1) {
            return cached_hash;
        }
        cached_hash = compute_hash();
        return cached_hash;
    }

    virtual int cmp(const Buffer* other) const;

    virtual bool isspace() const;
    virtual bool isalpha() const;
    virtual bool isdigit() const;
    virtual bool isalnum() const;
    virtual bool isupper() const;
    virtual bool islower() const;
    virtual bool isdecimal() const;
    virtual bool isnumeric() const;
    virtual bool isprintable() const;
    virtual bool istitle() const;

    virtual Buffer* collapse();
    virtual Buffer* optimize();

private:
    Py_hash_t compute_hash() const {
        Py_ssize_t len = length();
        Py_hash_t x = 0;
        Py_hash_t mult = 31;
        for (Py_ssize_t i = 0; i < len; i++) {
            uint32_t ch = value(i);
            x = x * mult + ch;
        }
        if (x == -1) {
            x = -2;
        }
        return x;
    }
};

struct LStrObject {
    PyObject_HEAD
    Buffer *buffer;
};

#endif // LSTRING_HXX
