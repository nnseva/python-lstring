/**
 * @file lstring_re_iterator.hxx
 * @brief Bidirectional iterator wrapper for lstring.L used by regex engines.
 *
 * This header declares LStrIteratorBuffer which provides a lightweight
 * bidirectional iterator view over an LStrObject's Buffer. The implementation
 * is intentionally minimal and assumes the underlying LStrObject and its
 * Buffer remain valid for the iterator's lifetime.
 */

#ifndef LSTRING_RE_ITERATOR_HXX
#define LSTRING_RE_ITERATOR_HXX

#include <Python.h>
#include "lstring.hxx"
#include "buffer.hxx"
#include <cppy/cppy.h>
#include <cstdint>
#include <cstddef>
#include <boost/iterator/iterator_facade.hpp>

// Forward-declare Buffer API used by the iterator.
// Buffer class is defined in buffer.hxx included by lstring.hxx transitively.

template<typename CharT>
class LStrIteratorBuffer : public boost::iterator_facade<
    LStrIteratorBuffer<CharT>,
    CharT,
    boost::random_access_traversal_tag,
    CharT
> {
public:
    // Default-constructible iterator (null owner). Boost.Regex instantiates
    // temporary/default iterators in some internal structures, so we must
    // provide a no-arg constructor. The resulting iterator compares equal to
    // other null iterators and has index 0.
    LStrIteratorBuffer()
        : obj_owner(), index(0)
    {}

    // Allow copying and moving; Boost.Regex and its internal helpers may
    // copy/assign iterator instances. Defaulted special members are
    // sufficient because cppy::ptr manages reference lifetime correctly.
    LStrIteratorBuffer(const LStrIteratorBuffer&) = default;
    LStrIteratorBuffer(LStrIteratorBuffer&&) noexcept = default;
    LStrIteratorBuffer& operator=(const LStrIteratorBuffer&) = default;
    LStrIteratorBuffer& operator=(LStrIteratorBuffer&&) noexcept = default;

    // Construct an iterator buffer that holds a reference to the LStrObject.
    // The cppy::ptr will own a strong reference (second arg true) to keep the
    // LStrObject alive while the iterator exists.
    explicit LStrIteratorBuffer(LStrObject *lobj, Py_ssize_t pos = 0)
        : obj_owner(reinterpret_cast<PyObject*>(lobj), true), index(pos)
    {}

    // Return the length (number of codepoints) of the underlying buffer.
    Py_ssize_t length() const {
        LStrObject *lobj = (LStrObject*)obj_owner.get();
        return lobj ? lobj->buffer->length() : 0;
    }

    void increment() {
        ++index;
    }

    void decrement() {
        --index;
    }

    void advance(std::ptrdiff_t n) {
        index += n;
    }

    std::ptrdiff_t distance_to(LStrIteratorBuffer const &other) const {
        // distance in number of codepoints from this to other
        return static_cast<std::ptrdiff_t>(other.index - index);
    }

    bool equal(LStrIteratorBuffer const &other) const {
        // Two iterators are equal when they refer to the same underlying LStrObject
        // and have the same index. Null owners compare equal when both null and index equal.
        return obj_owner.get() == other.obj_owner.get() && index == other.index;
    }

    CharT dereference() const {
        LStrObject *lobj = (LStrObject*)obj_owner.get();
        // Expect caller to ensure index in range.
        return static_cast<CharT>(lobj->buffer->value(index));
    }

private:
    // Own the LStrObject to keep it alive while iterator exists
    cppy::ptr obj_owner;
    Py_ssize_t index;
};

#endif // LSTRING_RE_ITERATOR_HXX
