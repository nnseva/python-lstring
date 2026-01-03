/**
 * @file lstring.hxx
 * @brief Declarations for the L object and forward declarations.
 */

#ifndef LSTRING_HXX
#define LSTRING_HXX

#include <Python.h>

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

/** Forward declaration of Buffer to avoid cyclic include */
class Buffer;
/** Forward declare StrBuffer concrete type used by make_str_buffer */
class StrBuffer;

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

/* Method table (defined in src/lstring_methods.cxx) */
extern PyMethodDef LStr_methods[];

/** Process-global optimize threshold declared in the module implementation. */
extern Py_ssize_t g_optimize_threshold;

#endif // LSTRING_HXX
