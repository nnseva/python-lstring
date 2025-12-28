/**
 * @file lstring_re_module.cxx
 * @brief Implementation of the lstring.re submodule.
 *
 * This file creates the Python submodule `lstring.re` and attaches it to the
 * parent `lstring` module during multi-phase initialization. The submodule
 * currently contains placeholder metadata and can be extended with regex
 * functions that operate on the `L` type.
 */

#include <Python.h>
#include "lstring_re.hxx"
#include "lstring_re_regex.hxx"
#include "lstring_utils.hxx"
#include <cppy/cppy.h>

// TODO: determine compatible CharT type for Boost.Regex usage with lstring.L
using CharT = wchar_t; // Placeholder; adjust as needed for target platform

// Use helper from lstring_utils.hxx: get_string_lstr_type()

// Forward declarations/definitions for Pattern are in lstring_re_pattern.hxx/cxx
#include "lstring_re_pattern.hxx"
#include "lstring_re_match.hxx"

// compile(pattern, flags=0, Match=None) -> Pattern
static PyObject* re_compile(PyObject *module, PyObject *args, PyObject *kwds) {
    PyObject *pattern_arg = nullptr;
    int flags = 0;
    PyObject *match_factory = nullptr;
    static char *kwlist[] = {(char*)"pattern", (char*)"flags", (char*)"Match", nullptr};
    
    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O|iO", kwlist, &pattern_arg, &flags, &match_factory)) {
        return nullptr;
    }
    
    // Get Pattern type from current module (lstring.re.Pattern)
    cppy::ptr pattern_type(PyObject_GetAttrString(module, "Pattern"));
    if (!pattern_type) return nullptr;
    
    // Create args tuple for Pattern constructor
    cppy::ptr ctor_args(Py_BuildValue("(Oi)", pattern_arg, flags));
    if (!ctor_args) return nullptr;
    
    // Create kwargs dict if Match factory is provided
    cppy::ptr kwargs;
    if (match_factory && match_factory != Py_None) {
        kwargs = cppy::ptr(Py_BuildValue("{sO}", "Match", match_factory));
        if (!kwargs) return nullptr;
    }
    
    return PyObject_Call(pattern_type.get(), ctor_args.get(), kwargs.get());
}

// match(pattern, string, flags=0) -> Match | None
static PyObject* re_match(PyObject *module, PyObject *args, PyObject *kwds) {
    PyObject *pattern_arg = nullptr;
    PyObject *string_arg = nullptr;
    int flags = 0;
    static char *kwlist[] = {(char*)"pattern", (char*)"string", (char*)"flags", nullptr};
    
    if (!PyArg_ParseTupleAndKeywords(args, kwds, "OO|i", kwlist, &pattern_arg, &string_arg, &flags)) {
        return nullptr;
    }
    
    // Compile pattern
    cppy::ptr compile_args(Py_BuildValue("(Oi)", pattern_arg, flags));
    if (!compile_args) return nullptr;
    
    cppy::ptr pattern_obj(re_compile(module, compile_args.get(), nullptr));
    if (!pattern_obj) return nullptr;
    
    // Call pattern.match(string)
    cppy::ptr match_args(Py_BuildValue("(O)", string_arg));
    if (!match_args) return nullptr;
    
    cppy::ptr match_method(PyObject_GetAttrString(pattern_obj.get(), "match"));
    if (!match_method) return nullptr;
    
    return PyObject_CallObject(match_method.get(), match_args.get());
}

// search(pattern, string, flags=0) -> Match | None
static PyObject* re_search(PyObject *module, PyObject *args, PyObject *kwds) {
    PyObject *pattern_arg = nullptr;
    PyObject *string_arg = nullptr;
    int flags = 0;
    static char *kwlist[] = {(char*)"pattern", (char*)"string", (char*)"flags", nullptr};
    
    if (!PyArg_ParseTupleAndKeywords(args, kwds, "OO|i", kwlist, &pattern_arg, &string_arg, &flags)) {
        return nullptr;
    }
    
    cppy::ptr compile_args(Py_BuildValue("(Oi)", pattern_arg, flags));
    if (!compile_args) return nullptr;
    
    cppy::ptr pattern_obj(re_compile(module, compile_args.get(), nullptr));
    if (!pattern_obj) return nullptr;
    
    cppy::ptr search_args(Py_BuildValue("(O)", string_arg));
    if (!search_args) return nullptr;
    
    cppy::ptr search_method(PyObject_GetAttrString(pattern_obj.get(), "search"));
    if (!search_method) return nullptr;
    
    return PyObject_CallObject(search_method.get(), search_args.get());
}

// fullmatch(pattern, string, flags=0) -> Match | None
static PyObject* re_fullmatch(PyObject *module, PyObject *args, PyObject *kwds) {
    PyObject *pattern_arg = nullptr;
    PyObject *string_arg = nullptr;
    int flags = 0;
    static char *kwlist[] = {(char*)"pattern", (char*)"string", (char*)"flags", nullptr};
    
    if (!PyArg_ParseTupleAndKeywords(args, kwds, "OO|i", kwlist, &pattern_arg, &string_arg, &flags)) {
        return nullptr;
    }
    
    cppy::ptr compile_args(Py_BuildValue("(Oi)", pattern_arg, flags));
    if (!compile_args) return nullptr;
    
    cppy::ptr pattern_obj(re_compile(module, compile_args.get(), nullptr));
    if (!pattern_obj) return nullptr;
    
    cppy::ptr fullmatch_args(Py_BuildValue("(O)", string_arg));
    if (!fullmatch_args) return nullptr;
    
    cppy::ptr fullmatch_method(PyObject_GetAttrString(pattern_obj.get(), "fullmatch"));
    if (!fullmatch_method) return nullptr;
    
    return PyObject_CallObject(fullmatch_method.get(), fullmatch_args.get());
}

// findall(pattern, string, flags=0) -> list
static PyObject* re_findall(PyObject *module, PyObject *args, PyObject *kwds) {
    PyObject *pattern_arg = nullptr;
    PyObject *string_arg = nullptr;
    int flags = 0;
    static char *kwlist[] = {(char*)"pattern", (char*)"string", (char*)"flags", nullptr};
    
    if (!PyArg_ParseTupleAndKeywords(args, kwds, "OO|i", kwlist, &pattern_arg, &string_arg, &flags)) {
        return nullptr;
    }
    
    cppy::ptr compile_args(Py_BuildValue("(Oi)", pattern_arg, flags));
    if (!compile_args) return nullptr;
    
    cppy::ptr pattern_obj(re_compile(module, compile_args.get(), nullptr));
    if (!pattern_obj) return nullptr;
    
    cppy::ptr findall_args(Py_BuildValue("(O)", string_arg));
    if (!findall_args) return nullptr;
    
    cppy::ptr findall_method(PyObject_GetAttrString(pattern_obj.get(), "findall"));
    if (!findall_method) return nullptr;
    
    return PyObject_CallObject(findall_method.get(), findall_args.get());
}

// finditer(pattern, string, flags=0) -> iterator
static PyObject* re_finditer(PyObject *module, PyObject *args, PyObject *kwds) {
    PyObject *pattern_arg = nullptr;
    PyObject *string_arg = nullptr;
    int flags = 0;
    static char *kwlist[] = {(char*)"pattern", (char*)"string", (char*)"flags", nullptr};
    
    if (!PyArg_ParseTupleAndKeywords(args, kwds, "OO|i", kwlist, &pattern_arg, &string_arg, &flags)) {
        return nullptr;
    }
    
    cppy::ptr compile_args(Py_BuildValue("(Oi)", pattern_arg, flags));
    if (!compile_args) return nullptr;
    
    cppy::ptr pattern_obj(re_compile(module, compile_args.get(), nullptr));
    if (!pattern_obj) return nullptr;
    
    cppy::ptr finditer_args(Py_BuildValue("(O)", string_arg));
    if (!finditer_args) return nullptr;
    
    cppy::ptr finditer_method(PyObject_GetAttrString(pattern_obj.get(), "finditer"));
    if (!finditer_method) return nullptr;
    
    return PyObject_CallObject(finditer_method.get(), finditer_args.get());
}

// sub(pattern, repl, string, count=0, flags=0) -> str
static PyObject* re_sub(PyObject *module, PyObject *args, PyObject *kwds) {
    PyObject *pattern_arg = nullptr;
    PyObject *repl_arg = nullptr;
    PyObject *string_arg = nullptr;
    int count = 0;
    int flags = 0;
    static char *kwlist[] = {(char*)"pattern", (char*)"repl", (char*)"string", (char*)"count", (char*)"flags", nullptr};
    
    if (!PyArg_ParseTupleAndKeywords(args, kwds, "OOO|ii", kwlist, &pattern_arg, &repl_arg, &string_arg, &count, &flags)) {
        return nullptr;
    }
    
    cppy::ptr compile_args(Py_BuildValue("(Oi)", pattern_arg, flags));
    if (!compile_args) return nullptr;
    
    cppy::ptr pattern_obj(re_compile(module, compile_args.get(), nullptr));
    if (!pattern_obj) return nullptr;
    
    cppy::ptr sub_args(Py_BuildValue("(OOi)", repl_arg, string_arg, count));
    if (!sub_args) return nullptr;
    
    cppy::ptr sub_method(PyObject_GetAttrString(pattern_obj.get(), "sub"));
    if (!sub_method) return nullptr;
    
    return PyObject_CallObject(sub_method.get(), sub_args.get());
}

// subn(pattern, repl, string, count=0, flags=0) -> (str, int)
static PyObject* re_subn(PyObject *module, PyObject *args, PyObject *kwds) {
    PyObject *pattern_arg = nullptr;
    PyObject *repl_arg = nullptr;
    PyObject *string_arg = nullptr;
    int count = 0;
    int flags = 0;
    static char *kwlist[] = {(char*)"pattern", (char*)"repl", (char*)"string", (char*)"count", (char*)"flags", nullptr};
    
    if (!PyArg_ParseTupleAndKeywords(args, kwds, "OOO|ii", kwlist, &pattern_arg, &repl_arg, &string_arg, &count, &flags)) {
        return nullptr;
    }
    
    cppy::ptr compile_args(Py_BuildValue("(Oi)", pattern_arg, flags));
    if (!compile_args) return nullptr;
    
    cppy::ptr pattern_obj(re_compile(module, compile_args.get(), nullptr));
    if (!pattern_obj) return nullptr;
    
    cppy::ptr subn_args(Py_BuildValue("(OOi)", repl_arg, string_arg, count));
    if (!subn_args) return nullptr;
    
    cppy::ptr subn_method(PyObject_GetAttrString(pattern_obj.get(), "subn"));
    if (!subn_method) return nullptr;
    
    return PyObject_CallObject(subn_method.get(), subn_args.get());
}

// split(pattern, string, maxsplit=0, flags=0) -> list
static PyObject* re_split(PyObject *module, PyObject *args, PyObject *kwds) {
    PyObject *pattern_arg = nullptr;
    PyObject *string_arg = nullptr;
    int maxsplit = 0;
    int flags = 0;
    static char *kwlist[] = {(char*)"pattern", (char*)"string", (char*)"maxsplit", (char*)"flags", nullptr};
    
    if (!PyArg_ParseTupleAndKeywords(args, kwds, "OO|ii", kwlist, &pattern_arg, &string_arg, &maxsplit, &flags)) {
        return nullptr;
    }
    
    cppy::ptr compile_args(Py_BuildValue("(Oi)", pattern_arg, flags));
    if (!compile_args) return nullptr;
    
    cppy::ptr pattern_obj(re_compile(module, compile_args.get(), nullptr));
    if (!pattern_obj) return nullptr;
    
    cppy::ptr split_args(Py_BuildValue("(Oi)", string_arg, maxsplit));
    if (!split_args) return nullptr;
    
    cppy::ptr split_method(PyObject_GetAttrString(pattern_obj.get(), "split"));
    if (!split_method) return nullptr;
    
    return PyObject_CallObject(split_method.get(), split_args.get());
}

static PyMethodDef lstring_re_methods[] = {
    {"compile", (PyCFunction)re_compile, METH_VARARGS | METH_KEYWORDS, "Compile a regular expression pattern."},
    {"match", (PyCFunction)re_match, METH_VARARGS | METH_KEYWORDS, "Try to apply the pattern at the start of the string."},
    {"search", (PyCFunction)re_search, METH_VARARGS | METH_KEYWORDS, "Scan through string looking for a match."},
    {"fullmatch", (PyCFunction)re_fullmatch, METH_VARARGS | METH_KEYWORDS, "Try to apply the pattern to all of the string."},
    {"findall", (PyCFunction)re_findall, METH_VARARGS | METH_KEYWORDS, "Return a list of all matches."},
    {"finditer", (PyCFunction)re_finditer, METH_VARARGS | METH_KEYWORDS, "Return an iterator over all matches."},
    {"sub", (PyCFunction)re_sub, METH_VARARGS | METH_KEYWORDS, "Replace occurrences of pattern in string."},
    {"subn", (PyCFunction)re_subn, METH_VARARGS | METH_KEYWORDS, "Replace occurrences of pattern in string, return (new_string, count)."},
    {"split", (PyCFunction)re_split, METH_VARARGS | METH_KEYWORDS, "Split string by occurrences of pattern."},
    {nullptr, nullptr, 0, nullptr}
};

// Module definition for the submodule
static struct PyModuleDef lstring_re_def = {
    PyModuleDef_HEAD_INIT,
    "_lstring.re",
    "Regular-expression helpers for lstring.L (submodule)",
    0,
    lstring_re_methods,
    nullptr,
    nullptr,
    nullptr,
    nullptr
};

// Create and initialize the submodule, attach to parent module as attribute 're'.
int lstring_re_mod_exec(PyObject *parent_module, const char *submodule_name) {
    cppy::ptr submodule(PyModule_Create(&lstring_re_def));
    if (!submodule) {
        return -1;
    }
    
    // Add the submodule to sys.modules for direct import (import _lstring.re)
    PyObject *sys_modules = PyImport_GetModuleDict();  // borrowed reference
    if (sys_modules) {
        if (PyDict_SetItemString(sys_modules, "_lstring.re", submodule.get()) < 0) {
            return -1;
        }
    }
    
    // Add the submodule to the parent module as attribute 're'
    if (PyModule_AddObject(parent_module, submodule_name, Py_NewRef(submodule.get())) < 0) {
        return -1;
    }

    // Optionally add a convenience attribute
    if (PyModule_AddStringConstant(submodule.get(), "__doc__", "Regex helpers for lstring.L") < 0) {
        return -1;
    }

    // Create and register Pattern type in the submodule (implementation
    // provided by lstring_re_pattern.cxx)
    if (lstring_re_register_pattern_type(submodule.get()) < 0) return -1;

    // Create and register Match type (stubbed implementation)
    if (lstring_re_register_match_type(submodule.get()) < 0) return -1;

    return 0;
}
