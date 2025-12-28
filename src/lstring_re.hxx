/**
 * @file lstring_re.hxx
 * @brief Declarations for the lstring.re submodule (regular expression helpers)
 *
 * This header provides forward declarations and shared types used by the
 * lstring.re implementation. It is intentionally lightweight now and will be
 * expanded as regex functionality is implemented.
 */
#ifndef LSTRING_RE_HXX
#define LSTRING_RE_HXX

#include <Python.h>

// Create the lstring.re submodule and attach it to the parent `lstring`
// module. The function returns 0 on success, -1 on failure (Python exception set).
int lstring_re_mod_exec(PyObject *parent_module, const char *submodule_name = "re");

#endif // LSTRING_RE_HXX
