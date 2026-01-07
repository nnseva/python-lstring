/**
 * @file lstring_re_regex.hxx
 * @brief Declaration of LStrRegexBuffer wrapper for compiled Boost.Regex objects.
 *
 * This header declares a thin C++ wrapper type intended to hold a compiled
 * Boost.Regex object. The concrete Boost includes are intentionally not pulled
 * into this header to keep compile-time dependencies small; implementation
 * files should include the Boost headers and implement the methods.
 */

#ifndef LSTRING_RE_REGEX_HXX  
#define LSTRING_RE_REGEX_HXX

#include <Python.h>
#include "lstring_re_iterator.hxx"
#include "lstring_re_pattern.hxx"

#ifdef LSTRING_RE_USE_PYTHON_TRAITS
    #include "lstring_re_python_traits.hxx"
#else
    #include "lstring_re_icu_traits.hxx"
#endif

#include "tptr.hxx"
#include <cppy/cppy.h>
#include <boost/regex/v5/regex.hpp>
#include <string>

template<typename CharT>
class LStrRegexBuffer {
public:
    // Construct and compile regex from the given LStrObject (pattern).
    // flags use boost::regex_constants::syntax_option_type values.
    explicit LStrRegexBuffer(LStrObject *pattern, int flags = 0)
        : re([&](){
            // Build regex directly from char32_t iterators over the LStrObject
            LStrIteratorBuffer<CharT> pbegin(pattern, 0);
            LStrIteratorBuffer<CharT> pend(pattern, pbegin.length());
            using re_t = decltype(re);
            return re_t(pbegin, pend, static_cast<boost::regex_constants::syntax_option_type>(flags));
        }())
    {
    }

    virtual ~LStrRegexBuffer() = default;

    // Store compiled regex directly
#ifdef LSTRING_RE_USE_PYTHON_TRAITS
    using traits_t = boost::regex_traits_wrapper<lstring_re::python_u32_regex_traits>;
#else
    using traits_t = boost::regex_traits_wrapper<lstring_re::icu_u32_regex_traits>;
#endif
    boost::basic_regex<CharT, traits_t> re;
};

// Lightweight holder for match results produced by Boost.Regex when matching
// against an `lstring.L`. This class is declared as a template so it can be
// instantiated with the same `CharT` used by `LStrRegexBuffer`. Only a
// default constructor and a virtual destructor are provided here as a
// placeholder; full implementation will be added later.
template<typename CharT>
class LStrMatchBuffer {
public:
    // Construct a match buffer that keeps references to the Pattern object
    // and the `lstring.L` (`where`) where the match was performed. Both
    // `cppy::ptr` wrappers are created with `owned=true` to take a new
    // reference.
    explicit LStrMatchBuffer(PyObject *pattern, PyObject *where, Py_ssize_t pos, Py_ssize_t endpos)
        : pattern(pattern, true), where(where, true), pos(pos), endpos(endpos), results()
    {}

    virtual ~LStrMatchBuffer() = default;

    // Reference to the Pattern that produced these results.
    tptr<PatternObject> pattern;
    // Reference to the subject `lstring.L` object where the search was run.
    tptr<LStrObject> where;
    // The start position used for this match.
    Py_ssize_t pos;
    // The end position used for this match.
    Py_ssize_t endpos;
    // Actual Boost.Regex match results. Holds iterators into the subject.
    boost::match_results<LStrIteratorBuffer<CharT>> results;
};

#endif // LSTRING_RE_REGEX_HXX
