#ifndef LSTRING_RE_MATCH_HXX
#define LSTRING_RE_MATCH_HXX

#include <Python.h>

// Forward-declare the LStrMatchBuffer template so callers can pass pointers
template<typename CharT>
class LStrMatchBuffer;

// Minimal Match object visible to other compilation units. The concrete
// match buffer pointer is stored as a void* and cast to the appropriate
// `LStrMatchBuffer<CharT>*` in the implementation.
struct MatchObject {
	PyObject_HEAD
	void *matchbuf;
};

// Register the Match type into the given submodule. Returns 0 on success
// or -1 on failure (and sets a Python exception).
int lstring_re_register_match_type(PyObject *submodule);

#endif // LSTRING_RE_MATCH_HXX
