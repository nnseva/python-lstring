/**
 * @file lstring.cxx
 * @brief Python C++ extension defining lstring.lstr - a lazy string class.
 */

#include <Python.h>
#include <cstdio>

#include "lstring.hxx"
#include "buffer.hxx"
#include "str_buffer.hxx"
#include "join_buffer.hxx"
#include "mul_buffer.hxx"
#include "slice_buffer.hxx"

/**
 * @brief Global process-wide optimize threshold.
 *
 * The threshold controls when small lazy results are collapsed into
 * concrete contiguous Python strings. It is intentionally a process-global
 * C variable for very fast hot-path checks. This breaks sub-interpreter
 * isolation: all interpreters in the process share this value.
 */
static Py_ssize_t g_optimize_threshold = 0;

// Module-level accessors (exposed to Python). These functions access the
// global C variable above. We expose them as module functions rather than
// attempting to create a module-level property; functions are simpler and
// sufficient for tests and control.
static PyObject* lstring_get_optimize_threshold(PyObject *self, PyObject *Py_UNUSED(ignored));
static PyObject* lstring_set_optimize_threshold(PyObject *self, PyObject *arg);

/**
 * @name Per-module state
 * Helpers for storing module-local state.
 */
typedef struct {
    PyObject *LStrType;
} lstring_state;

/**
 * @brief Retrieve the per-module state for the lstring module.
 *
 * @param module The module object.
 * @return Pointer to the module's `lstring_state` or nullptr on error.
 */
static inline lstring_state* get_lstring_state(PyObject *module) {
    return (lstring_state*)PyModule_GetState(module);
}

// Type methods (forward declarations)
// Note: these are forward declarations only; keep the header minimal to avoid
// emitting an extra Doxygen section for declarations.
static PyObject* LStr_new(PyTypeObject *type, PyObject *args, PyObject *kwds);
static void LStr_dealloc(LStrObject *self);
static Py_hash_t LStr_hash(LStrObject *self);
static PyObject* LStr_repr(LStrObject *self);
static PyObject* LStr_add(PyObject *left, PyObject *right);
static PyObject* LStr_mul(PyObject *left, PyObject *right);
static PyObject* LStr_str(LStrObject *self);
static Py_ssize_t LStr_sq_length(PyObject *self);
static PyObject* LStr_subscript(PyObject *self_obj, PyObject *key);
static PyObject* LStr_richcompare(PyObject *a, PyObject *b, int op);
static PyObject* LStr_collapse(LStrObject *self, PyObject *Py_UNUSED(ignored));
static void lstr_optimize(LStrObject *self);
void lstr_collapse(LStrObject *self);


/**
 * @name Type slots
 * Methods and slots exposed on the lstr type.
 */
/**
 * @brief Method table for the lstr type.
 *
 * Contains Python-callable methods exposed on the `_lstr` type. Each entry
 * maps a method name to a C function and calling convention.
 */
static PyMethodDef LStr_methods[] = {
    {"collapse", (PyCFunction)LStr_collapse, METH_NOARGS, "Collapse internal buffer to a contiguous str buffer"},
    {nullptr, nullptr, 0, nullptr}
};

/**
 * @brief Type slots for `_lstr` used to create the heap type from spec.
 *
 * These slots wire up tp_new, tp_dealloc, numeric/mapping/sequence
 * protocol handlers and other type-level metadata.
 */
static PyType_Slot LStr_slots[] = {
    {Py_tp_new,       (void*)LStr_new},
    {Py_tp_dealloc,   (void*)LStr_dealloc},
    {Py_tp_hash,      (void*)LStr_hash},
    {Py_tp_repr,      (void*)LStr_repr},
    {Py_tp_str,       (void*)LStr_str},   // conversion to str
    {Py_tp_methods,   (void*)LStr_methods},
    {Py_tp_doc,       (void*)"lstr is a lazy string class that defers direct access to its internal buffer"},
    {Py_nb_add,       (void*)LStr_add},   // operator +
    {Py_nb_multiply,  (void*)LStr_mul},   // operator *
    {Py_tp_richcompare, (void*)LStr_richcompare},

    // Sequence protocol: only length is provided; concatenation/repeat
    // are implemented via the number protocol (nb_add / nb_multiply).
    {Py_sq_length, (void*)LStr_sq_length},

    // Mapping protocol: lstr[index] lstr[start:stop:step]
    {Py_mp_subscript, (void*)LStr_subscript},
    {0, nullptr}
};

/**
 * @brief PyType_Spec for the `_lstr` heap type.
 *
 * This spec is passed to PyType_FromSpec during module initialization to
 * create a concrete type object for `_lstr`.
 */
static PyType_Spec LStr_spec = {
    "lstring.lstr",
    sizeof(LStrObject),
    0,
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,
    LStr_slots
};

/**
 * @name Implementation
 * Helper implementations for buffer creation and lstr operations.
 */
/**
 * @brief Construct appropriate StrBuffer based on Python string kind.
 * @param py_str A Python str object
 * @return StrBuffer* or nullptr on error (sets PyErr)
 */
/**
 * @brief Build a StrBuffer wrapper for a Python str.
 *
 * The returned StrBuffer takes ownership of any required state and wraps
 * the provided Python string. On error, nullptr is returned and a Python
 * exception is set.
 *
 * @param py_str Python str object (borrowed reference)
 * @return New StrBuffer* or nullptr on error.
 */
static StrBuffer* make_str_buffer(PyObject *py_str) {
    switch (PyUnicode_KIND(py_str)) {
        case PyUnicode_1BYTE_KIND:
            return new Str8Buffer(py_str);
        case PyUnicode_2BYTE_KIND:
            return new Str16Buffer(py_str);
        case PyUnicode_4BYTE_KIND:
            return new Str32Buffer(py_str);
        default:
            PyErr_SetString(PyExc_RuntimeError, "Unsupported Unicode kind");
            return nullptr;
    }
}

// ---------- LStr constructors / destructors ----------
/**
 * @brief __new__ implementation for `_lstr`.
 *
 * Expects a single Python str argument and creates a new `_lstr` instance
 * wrapping a StrBuffer that references the string.
 */
static PyObject* LStr_new(PyTypeObject *type, PyObject *args, PyObject *kwds) {
    static const char *kwlist[] = {"string", nullptr};
    PyObject *py_str = nullptr;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O:str", (char**)kwlist, &py_str)) {
        return nullptr;
    }
    if (!PyUnicode_Check(py_str)) {
        PyErr_SetString(PyExc_TypeError, "argument must be str");
        return nullptr;
    }

    LStrObject *self = (LStrObject*)type->tp_alloc(type, 0);
    if (!self) return nullptr;
    cppy::ptr self_owner((PyObject*)self);

    try {
        self->buffer = make_str_buffer(py_str);
        if (!self->buffer) return nullptr; // make_str_buffer sets PyErr on failure
    } catch (const std::exception &e) {
        PyErr_SetString(PyExc_RuntimeError, e.what());
        return nullptr;
    } catch (...) {
        PyErr_SetString(PyExc_RuntimeError, "Buffer allocation failed");
        return nullptr;
    }

    return self_owner.release();
}

/**
 * @brief Deallocator for `_lstr` instances.
 *
 * Frees the internal Buffer and releases the object memory.
 */
static void LStr_dealloc(LStrObject *self) {
    delete self->buffer;
    self->buffer = nullptr;
    Py_TYPE(self)->tp_free((PyObject*)self);
}

// ---------- LStr hash, length and repr ----------
/**
 * @brief Hash function for `_lstr`.
 *
 * Delegates to the underlying Buffer's cached hash implementation.
 */
static Py_hash_t LStr_hash(LStrObject *self) {
    if (!self->buffer) {
        PyErr_SetString(PyExc_RuntimeError, "lstr has no buffer");
        return -1;
    }
    return self->buffer->hash();
}

/**
 * @brief Sequence protocol length for `_lstr`.
 *
 * Returns the number of code points in the underlying buffer.
 */
static Py_ssize_t LStr_sq_length(PyObject *self) {
    return ((LStrObject*)self)->buffer->length();
}

/**
 * @brief repr(self) implementation for `_lstr`.
 *
 * Produces a Python string representing the lstr; delegates to Buffer::repr.
 */
static PyObject* LStr_repr(LStrObject *self) {
    if (!self->buffer) {
        PyErr_SetString(PyExc_RuntimeError, "lstr has no buffer");
        return nullptr;
    }

    return self->buffer->repr();
}

/**
 * @brief Convert any non-StrBuffer into a concrete StrBuffer backed by a
 *        Python str.
 *
 * If the buffer already wraps a Python string, this is a no-op. On error
 * this function propagates the Python exception and leaves the object
 * unchanged.
 */
void lstr_collapse(LStrObject *self) {
    if (!self || !self->buffer) return;
    if (self->buffer->is_str()) return; // already a StrBuffer

    cppy::ptr py( LStr_str(self) );
    if (!py) {
        // propagate error to caller by leaving state unchanged
        return;
    }

    // Create new StrBuffer from the Python string
    StrBuffer *new_buf = make_str_buffer(py.get());
    if (!new_buf) {
        return; // make_str_buffer sets an error
    }

    // Replace buffer
    delete self->buffer;
    self->buffer = new_buf;
}

/**
 * @brief Try to collapse small lazy buffers into concrete StrBuffers.
 *
 * Uses the process-global `g_optimize_threshold` to decide whether to
 * collapse. If the threshold is inactive (<= 0), this is a no-op.
 */
static void lstr_optimize(LStrObject *self) {
    if (!self || !self->buffer) return;
    if (self->buffer->is_str()) return;
    // Use the global C variable for threshold (very fast). See comment by
    // declaration of g_optimize_threshold about sub-interpreter isolation.
    if (g_optimize_threshold <= 0) return;

    Py_ssize_t len = (Py_ssize_t)self->buffer->length();
    if (len < g_optimize_threshold) lstr_collapse(self);
}

// ---------- Slicing via mapping (mp_subscript) ----------
/**
 * @brief Support for indexing and slicing (`obj[index]` / `obj[start:stop:step]`).
 *
 * Returns a newly allocated `str` for single-index lookups and a new
 * `_lstr` instance for slices.
 */
static PyObject* LStr_subscript(PyObject *self_obj, PyObject *key) {
    LStrObject *self = (LStrObject*)self_obj;
    Py_ssize_t length = self->buffer->length();

    if (PyLong_Check(key)) {
        // Integer index
        Py_ssize_t index = PyLong_AsSsize_t(key);
        if (index == -1 && PyErr_Occurred()) return nullptr;

        if (index < 0) index += length;
        if (index < 0 || index >= length) {
            PyErr_SetString(PyExc_IndexError, "lstr index out of range");
            return nullptr;
        }
        uint32_t ch = self->buffer->value(index);
        return PyUnicode_FromOrdinal(ch);
    }

    if (!PySlice_Check(key)) {
        PyErr_SetString(PyExc_TypeError, "lstr index type not supported");
        return nullptr;
    }
    // Slice
    Py_ssize_t start, end, step;
    if (PySlice_Unpack(key, &start, &end, &step) < 0) {
        return nullptr;  // generate exception set by Unpack
    }
    PySlice_AdjustIndices(length, &start, &end, step);
    
    if (step == 0) {
        PyErr_SetString(PyExc_ValueError, "slice step cannot be zero");
        return nullptr;
    }

    PyTypeObject *type = Py_TYPE(self);
    LStrObject *result = (LStrObject*)type->tp_alloc(type, 0);
    if (!result) return nullptr;
    cppy::ptr result_owner((PyObject*)result);

    try {
        if (step == 1) {
            result->buffer = new Slice1Buffer(self_obj, start, end);
        } else {
            result->buffer = new SliceBuffer(self_obj, start, end, step);
        }
    } catch (const std::exception &e) {
        PyErr_SetString(PyExc_RuntimeError, e.what());
        return nullptr;
    } catch (...) {
        PyErr_SetString(PyExc_RuntimeError, "slice creation failed");
        return nullptr;
    }

    // Try to optimize/collapse small results
    lstr_optimize(result);

    return result_owner.release();
}

// Python-exposed method wrapper for collapse()
/**
 * @brief Python method wrapper: collapse(self)
 *
 * Exposes the internal `lstr_collapse` helper as a Python-callable
 * method.
 */
static PyObject* LStr_collapse(LStrObject *self, PyObject *Py_UNUSED(ignored)) {
    if (!self) {
        PyErr_SetString(PyExc_RuntimeError, "invalid lstr object");
        return nullptr;
    }
    lstr_collapse(self);
    if (PyErr_Occurred()) return nullptr;
    Py_RETURN_NONE;
}

// ---------- Concatenation (operator +) ----------
/**
 * @brief Numeric add handler for `_lstr`.
 *
 * Supports `_lstr + _lstr` and mixed `_lstr + str` / `str + _lstr` where
 * a Python `str` operand is wrapped into a temporary `_lstr` backed by a
 * StrBuffer.
 */
static PyObject* LStr_add(PyObject *left, PyObject *right) {
    // Allow mixing `_lstr` and Python `str`.
    bool left_is_str = PyUnicode_Check(left);
    bool right_is_str = PyUnicode_Check(right);

    // Helper: detect whether an object is our lstr type by checking for
    // the `collapse` attribute on its type (cheap heuristic used elsewhere).
    auto is_lstr_type = [](PyObject *obj) -> bool {
        return PyObject_HasAttrString((PyObject*)Py_TYPE(obj), "collapse");
    };

    // Reject str+str
    if (left_is_str && right_is_str) {
        PyErr_SetString(PyExc_TypeError, "both operands cannot be Python str");
        return nullptr;
    }

    // Determine lstr type and validate operands. If one operand is a Python
    // str, the other must be an lstr. Otherwise both operands must be the
    // same lstr type. For unsupported combos, return a clear error that
    // includes the Python-level type names.
    PyTypeObject *type = nullptr;
    if (!left_is_str && !right_is_str && Py_TYPE(left) != Py_TYPE(right)) {
        // neither is Python str: require both be same lstr type
        cppy::ptr lt(PyObject_Type(left), true);
        cppy::ptr rt(PyObject_Type(right), true);
        PyErr_Format(PyExc_TypeError, "Operation %R + %R not supported", lt.get(), rt.get());
        return nullptr;
    }

    if (left_is_str) {
        type = Py_TYPE(right);
    } else {
        type = Py_TYPE(left);
    }
    cppy::ptr left_owner, right_owner;
    if(left_is_str) {
        PyObject *new_left = type->tp_alloc(type, 0);
        if (!new_left) return nullptr;
        left_owner = cppy::ptr(new_left);
        right_owner = cppy::ptr(right, true);
        StrBuffer *buf = make_str_buffer(left);
        if(!buf) return nullptr; // make_str_buffer sets PyErr on failure
        ((LStrObject *)left_owner.get())->buffer = buf;
    } else if(right_is_str) {
        PyObject *new_right = type->tp_alloc(type, 0);
        if (!new_right) return nullptr;
        right_owner = cppy::ptr(new_right);
        left_owner = cppy::ptr(left, true);
        StrBuffer *buf = make_str_buffer(right);
        if(!buf) return nullptr; // make_str_buffer sets PyErr on failure
        ((LStrObject *)right_owner.get())->buffer = buf;
    } else {
        left_owner = cppy::ptr(left, true);
        right_owner = cppy::ptr(right, true);
    }

    // Allocate result object of the lstr type
    LStrObject *result = (LStrObject*)type->tp_alloc(type, 0);
    if (!result) return nullptr;
    cppy::ptr result_owner((PyObject*)result);

    try {
        result->buffer = new JoinBuffer(left_owner.get(), right_owner.get());
    } catch (const std::exception &e) {
        PyErr_SetString(PyExc_RuntimeError, e.what());
        return nullptr;
    } catch (...) {
        PyErr_SetString(PyExc_RuntimeError, "JoinBuffer allocation failed");
        return nullptr;
    }

    // Try to optimize/collapse small results
    lstr_optimize(result);

    return result_owner.release();
}

// ---------- Multiplication (operator *) ----------
/**
 * @brief Numeric multiply (repeat) handler for `_lstr`.
 *
 * Supports `_lstr * int` and `int * _lstr`.
 */
static PyObject* LStr_mul(PyObject *left, PyObject *right) {
    PyObject *lstr_obj = nullptr;
    PyObject *count_obj = nullptr;

    // Decide which operand is the index
    if (PyLong_Check(right)) {
        lstr_obj = left;
        count_obj = right;
    } else if (PyLong_Check(left)) {
        lstr_obj = right;
        count_obj = left;
    } else {
        PyErr_SetString(PyExc_TypeError,
                        "lstr multiplication requires an integer operand");
        return nullptr;
    }

    // Convert directly to Py_ssize_t
    Py_ssize_t repeat_count = PyLong_AsSsize_t(count_obj);
    if (repeat_count == -1 && PyErr_Occurred()) {
        return nullptr;
    }
    if (repeat_count < 0) {
        PyErr_SetString(PyExc_RuntimeError,
                        "lstr repeat count must be non-negative");
        return nullptr;
    }

    // Allocate result
    PyTypeObject *type = Py_TYPE(lstr_obj);
    LStrObject *result = (LStrObject*)type->tp_alloc(type, 0);
    if (!result) return nullptr;
    cppy::ptr result_owner((PyObject*)result);

    try {
        result->buffer = new MulBuffer(lstr_obj, repeat_count);
    } catch (const std::exception &e) {
        PyErr_SetString(PyExc_RuntimeError, e.what());
        return nullptr;
    } catch (...) {
        PyErr_SetString(PyExc_RuntimeError, "lstr multiplication failed");
        return nullptr;
    }

    // Try to optimize/collapse small results
    lstr_optimize(result);

    return result_owner.release();
}

// ---------- Compare ----------
/**
 * @brief Rich comparison implementation for `_lstr` instances.
 *
 * Implements equality/ordering by delegating to the underlying Buffer
 * comparison. For EQ/NE a cheap hash comparison is attempted first.
 */
static PyObject* LStr_richcompare(PyObject *a, PyObject *b, int op) {
    if (Py_TYPE(a) != Py_TYPE(b)) {
        Py_RETURN_NOTIMPLEMENTED;
    }

    LStrObject *la = (LStrObject*)a;
    LStrObject *lb = (LStrObject*)b;
    Buffer *ba = la->buffer;
    Buffer *bb = lb->buffer;

    if (!ba || !bb) {
        PyErr_SetString(PyExc_RuntimeError, "lstr has no buffer");
        return nullptr;
    }

    // Optimize equality/inequality with hash
    if (op == Py_EQ || op == Py_NE) {
        if (ba->hash() != bb->hash()) {
            if (op == Py_EQ) Py_RETURN_FALSE;
            else Py_RETURN_TRUE;
        }
    }

    int cmp = ba->cmp(bb);

    switch (op) {
        case Py_EQ: if (cmp == 0) Py_RETURN_TRUE; else Py_RETURN_FALSE;
        case Py_NE: if (cmp != 0) Py_RETURN_TRUE; else Py_RETURN_FALSE;
        case Py_LT: if (cmp < 0)  Py_RETURN_TRUE; else Py_RETURN_FALSE;
        case Py_LE: if (cmp <= 0) Py_RETURN_TRUE; else Py_RETURN_FALSE;
        case Py_GT: if (cmp > 0)  Py_RETURN_TRUE; else Py_RETURN_FALSE;
        case Py_GE: if (cmp >= 0) Py_RETURN_TRUE; else Py_RETURN_FALSE;
        default: Py_RETURN_NOTIMPLEMENTED;
    }
}

// ---------- Conversion to Python str ----------
/**
 * @brief Materialize the `_lstr` as a concrete Python `str`.
 *
 * If the underlying Buffer already wraps a Python string, that object is
 * returned with an owned reference; otherwise a new Python string is
 * created and populated from the Buffer's contents.
 */
static PyObject* LStr_str(LStrObject *self) {
    Buffer *buf = self->buffer;
    if (!buf) {
        PyErr_SetString(PyExc_RuntimeError, "lstr has no buffer");
        return nullptr;
    }

    // Shortcut: if buffer already wraps a Python str (StrBuffer), return it
    // directly (with an owned reference) to avoid copying.
    if (buf->is_str()) {
        // Safe to dynamic_cast because StrBuffer overrides is_str()
        StrBuffer *sbuf = static_cast<StrBuffer*>(buf);
        cppy::ptr py(sbuf->get_str(), true);
        return py.release();
    }

    uint32_t len = buf->length();
    int kind = buf->unicode_kind();

    PyObject *py_str = nullptr;
    if (kind == PyUnicode_1BYTE_KIND) {
        py_str = PyUnicode_New(len, 0xFF);
        if (!py_str) return nullptr;
        uint8_t *data = reinterpret_cast<uint8_t*>(PyUnicode_DATA(py_str));
        buf->copy(data, 0, len);
    } else if (kind == PyUnicode_2BYTE_KIND) {
        py_str = PyUnicode_New(len, 0xFFFF);
        if (!py_str) return nullptr;
        uint16_t *data = reinterpret_cast<uint16_t*>(PyUnicode_DATA(py_str));
        buf->copy(data, 0, len);
    } else if (kind == PyUnicode_4BYTE_KIND) {
        py_str = PyUnicode_New(len, 0x10FFFF);
        if (!py_str) return nullptr;
        uint32_t *data = reinterpret_cast<uint32_t*>(PyUnicode_DATA(py_str));
        buf->copy(data, 0, len);
    } else {
        PyErr_SetString(PyExc_RuntimeError, "Unsupported buffer kind");
        return nullptr;
    }

    return py_str;
}

// ---------- Module methods ----------

/**
 * @brief Get the current process-global optimize threshold.
 *
 * Returns an int for the current value of `g_optimize_threshold`.
 */
static PyObject* lstring_get_optimize_threshold(PyObject *self, PyObject *Py_UNUSED(ignored)) {
    return PyLong_FromSsize_t(g_optimize_threshold);
}

/**
 * @brief Set the process-global optimize threshold.
 *
 * Accepts an int value or `None` to clear (disable) the threshold.
 */
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

/**
 * @brief Module-level functions exposed by the `lstring` module.
 */
static PyMethodDef lstring_module_methods[] = {
    {"get_optimize_threshold", (PyCFunction)lstring_get_optimize_threshold, METH_NOARGS, "Get global C optimize threshold (process-global)"},
    {"set_optimize_threshold", (PyCFunction)lstring_set_optimize_threshold, METH_O, "Set global C optimize threshold (process-global)"},
    {nullptr, nullptr, 0, nullptr}
};

// ---------- GC support ----------
/**
 * @brief GC traverse callback for the module state.
 *
 * Invoked by the interpreter's GC machinery to visit module-owned Python
 * objects.
 */
static int lstring_traverse(PyObject *module, visitproc visit, void *arg) {
    lstring_state *st = get_lstring_state(module);
    if (st && st->LStrType) return visit(st->LStrType, arg);
    return 0;
}

/**
 * @brief GC clear callback for the module state.
 *
 * Releases owned references held in the module state.
 */
static int lstring_clear(PyObject *module) {
    lstring_state *st = get_lstring_state(module);
    Py_CLEAR(st->LStrType);
    return 0;
}

/**
 * @brief Module free callback invoked when the module is destroyed.
 */
static void lstring_free(void *module) {
    lstring_clear((PyObject*)module);
}

// ---------- Multi-phase init ----------
/**
 * @brief Module exec function for multiphase initialization.
 *
 * Creates the `_lstr` heap type from `LStr_spec` and stores it in the
 * module state under the name `_lstr`.
 */
static int lstring_mod_exec(PyObject *module) {
    lstring_state *st = get_lstring_state(module);
    PyObject *type_obj = PyType_FromSpec(&LStr_spec);
    if (!type_obj) return -1;
    st->LStrType = type_obj;
    // Note: optimization threshold is controlled by the module-level
    // accessors which manipulate the process-global C variable
    // `g_optimize_threshold`. Use `lstring.get_optimize_threshold()` and
    // `lstring.set_optimize_threshold()` to query or change this value.
    // Using a process-global C variable provides the fastest hot-path
    // checks but breaks sub-interpreter isolation: all interpreters in
    // the process share the same threshold value.

    if (PyModule_AddObject(module, "_lstr", st->LStrType) < 0) {
        Py_CLEAR(st->LStrType);
        return -1;
    }
    return 0;
}

/**
 * @brief Slots for module initialization (used by multi-phase init).
 */
static PyModuleDef_Slot lstring_slots[] = {
    {Py_mod_exec,   (void*)lstring_mod_exec},
    {0, nullptr}
};

/**
 * @brief Module definition for `lstring`.
 */
static struct PyModuleDef lstring_def = {
    PyModuleDef_HEAD_INIT,
    "lstring",
    "Module providing lazy string class 'lstr' for deferred buffer access",
    sizeof(lstring_state),
    lstring_module_methods,
    lstring_slots,
    lstring_traverse,
    lstring_clear,
    lstring_free
};

/**
 * @brief Module initialization entry point.
 *
 * Returns a new module object initialized from `lstring_def`.
 */
PyMODINIT_FUNC PyInit_lstring(void) {
    return PyModuleDef_Init(&lstring_def);
}
