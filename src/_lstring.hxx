#ifndef _LSTRING_XXH_
#define _LSTRING_XXH_
/** Internal header for the lstring module */

#include <Python.h>
#include "lstring/lstring.hxx"
#include "tptr.hxx"

/* Method table (defined in src/lstring_methods.cxx) */
extern PyMethodDef LStr_methods[];

/** Process-global optimize threshold declared in the module implementation. */
extern Py_ssize_t LStr_optimize_threshold;

/**
 * @brief Build a balanced JoinBuffer tree for concatenation.
 *
 * Defined in src/lstring_concat.cxx.
 */
tptr<LStrObject> concat_balanced(PyTypeObject* type, const tptr<LStrObject>& left, const tptr<LStrObject>& right);

#endif // _LSTRING_XXH_
