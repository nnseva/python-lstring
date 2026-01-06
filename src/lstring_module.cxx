/**
 * @file lstring_module.cxx
 * @brief Module-level initialization and helpers for the lstring module.
 */

#include <Python.h>
#include <cstdio>
#include <cstdlib>

#include <cppy/ptr.h>

#include <unicode/uclean.h>
#include <unicode/putil.h>

#include "lstring.hxx"
#include "lstring_re.hxx"

/**
 * @brief Module-local state structure used by the multi-phase init.
 */
struct lstring_state {
    PyObject *LStrType;
};

// The LStr_spec is defined in the implementation file for the type.
extern PyType_Spec LStr_spec;

// Factory created in lstring_re_module.cxx; exported with C linkage.
extern "C" PyObject* lstring_re_create_submodule();

/**
 * @brief Global process-wide optimize threshold.
 */
Py_ssize_t g_optimize_threshold = 0;

// Module-level accessors (exposed to Python).
static PyObject* lstring_get_optimize_threshold(PyObject *self, PyObject *Py_UNUSED(ignored)) {
    return PyLong_FromSsize_t(g_optimize_threshold);
}

static PyObject* lstring_set_optimize_threshold(PyObject *self, PyObject *arg) {
    if (arg == Py_None) {
        g_optimize_threshold = 0;
        Py_RETURN_NONE;
    }
    if (!PyLong_Check(arg)) {
        PyErr_SetString(PyExc_TypeError, "optimize_threshold must be int or None");
        return nullptr;
    }
    Py_ssize_t v = PyLong_AsSsize_t(arg);
    if (v == -1 && PyErr_Occurred()) return nullptr;
    g_optimize_threshold = v;
    Py_RETURN_NONE;
}

/* Per-module state is declared in lstring.hxx; provide the definition
 * for the getter so other translation units can call it.
 */
inline static lstring_state* get_lstring_state(PyObject *module) {
    return (lstring_state*)PyModule_GetState(module);
}

// Module-level functions table
static PyMethodDef lstring_module_methods[] = {
    {"get_optimize_threshold", (PyCFunction)lstring_get_optimize_threshold, METH_NOARGS, "Get global C optimize threshold (process-global)"},
    {"set_optimize_threshold", (PyCFunction)lstring_set_optimize_threshold, METH_O, "Set global C optimize threshold (process-global)"},
    {nullptr, nullptr, 0, nullptr}
};

// GC callbacks
static int lstring_traverse(PyObject *module, visitproc visit, void *arg) {
    lstring_state *st = get_lstring_state(module);
    if (st && st->LStrType) return visit(st->LStrType, arg);
    return 0;
}

static int lstring_clear(PyObject *module) {
    lstring_state *st = get_lstring_state(module);
    Py_CLEAR(st->LStrType);
    return 0;
}

static void lstring_free(void *module) {
    lstring_clear((PyObject*)module);
}

static int lstring_init_icu_data_dir() {
    // If user already provided ICU_DATA, respect it.
    const char* env_icu_data = std::getenv("ICU_DATA");
    if (env_icu_data && env_icu_data[0]) {
        u_setDataDirectory(env_icu_data);
        UErrorCode status = U_ZERO_ERROR;
        u_init(&status);
        if (U_FAILURE(status)) {
            PyErr_Format(PyExc_RuntimeError, "ICU initialization failed (ICU_DATA=%s)", env_icu_data);
            return -1;
        }
        return 0;
    }

    // Avoid importing `lstring` (it imports `_lstring`). Use importlib.util.find_spec.
    cppy::ptr importlib_util(PyImport_ImportModule("importlib.util"));
    if (!importlib_util.get()) {
        return -1;
    }
    cppy::ptr find_spec(PyObject_GetAttrString(importlib_util.get(), "find_spec"));
    if (!find_spec.get()) {
        return -1;
    }
    cppy::ptr spec(PyObject_CallFunction(find_spec.get(), "s", "lstring"));
    if (!spec.get()) {
        return -1;
    }
    if (spec.get() == Py_None) {
        // If lstring package isn't present, ICU may still work if system data is available.
        return 0;
    }

    cppy::ptr origin(PyObject_GetAttrString(spec.get(), "origin"));
    if (!origin.get() || origin.get() == Py_None) {
        return 0;
    }

    cppy::ptr os_path(PyImport_ImportModule("os.path"));
    if (!os_path.get()) {
        return -1;
    }
    cppy::ptr pkg_dir(PyObject_CallMethod(os_path.get(), "dirname", "O", origin.get()));
    if (!pkg_dir.get()) {
        return -1;
    }
    cppy::ptr data_dir_obj(PyObject_CallMethod(os_path.get(), "join", "Os", pkg_dir.get(), "_icu_data"));
    if (!data_dir_obj.get()) {
        return -1;
    }

    const char* data_dir = PyUnicode_AsUTF8(data_dir_obj.get());
    if (!data_dir) {
        return -1;
    }

    u_setDataDirectory(data_dir);
    UErrorCode status = U_ZERO_ERROR;
    u_init(&status);
    if (U_FAILURE(status)) {
        PyErr_Format(PyExc_RuntimeError, "ICU initialization failed (data dir: %s)", data_dir);
        return -1;
    }
    return 0;
}

// Module exec: create the L heap type from the PyType_Spec and store it in the module state
static int lstring_mod_exec(PyObject *module) {
    if (lstring_init_icu_data_dir() < 0) {
        return -1;
    }
    lstring_state *st = get_lstring_state(module);
    PyObject *type_obj = PyType_FromSpec(&LStr_spec);
    if (!type_obj) return -1;
    st->LStrType = type_obj;

    if (PyModule_AddObject(module, "L", st->LStrType) < 0) {
        Py_CLEAR(st->LStrType);
        return -1;
    }

    // Add CharClass constants
    if (PyModule_AddIntConstant(module, "CHAR_SPACE", CHAR_SPACE) < 0) return -1;
    if (PyModule_AddIntConstant(module, "CHAR_ALPHA", CHAR_ALPHA) < 0) return -1;
    if (PyModule_AddIntConstant(module, "CHAR_DIGIT", CHAR_DIGIT) < 0) return -1;
    if (PyModule_AddIntConstant(module, "CHAR_ALNUM", CHAR_ALNUM) < 0) return -1;
    if (PyModule_AddIntConstant(module, "CHAR_LOWER", CHAR_LOWER) < 0) return -1;
    if (PyModule_AddIntConstant(module, "CHAR_UPPER", CHAR_UPPER) < 0) return -1;
    if (PyModule_AddIntConstant(module, "CHAR_DECIMAL", CHAR_DECIMAL) < 0) return -1;
    if (PyModule_AddIntConstant(module, "CHAR_NUMERIC", CHAR_NUMERIC) < 0) return -1;
    if (PyModule_AddIntConstant(module, "CHAR_PRINTABLE", CHAR_PRINTABLE) < 0) return -1;

    if (lstring_re_mod_exec(module) < 0) {
        return -1;
    }
    return 0;
}

/**
 * @name Type slots
 * Methods and slots exposed on the L type.
 */
static PyModuleDef_Slot lstring_slots[] = {
    {Py_mod_exec,   (void*)lstring_mod_exec},
    {0, nullptr}
};

static struct PyModuleDef lstring_def = {
    PyModuleDef_HEAD_INIT,
    "_lstring",
    "Module providing lazy string class 'L' for deferred buffer access",
    sizeof(lstring_state),
    lstring_module_methods,
    lstring_slots,
    lstring_traverse,
    lstring_clear,
    lstring_free
};

PyMODINIT_FUNC PyInit__lstring(void) {
    return PyModuleDef_Init(&lstring_def);
}
