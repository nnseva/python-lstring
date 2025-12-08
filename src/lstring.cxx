// lstring.cxx
//
// Python C++ extension defining lstring.lstr class - lazy string.

#include "lstring.hxx"
#include "buffer.hxx"
#include "join_buffer.hxx"
#include "mul_buffer.hxx"
#include "slice_buffer.hxx"

#include <Python.h>
#include <stdexcept>
#include <cstdio>

// ---------- Per-module state ----------
typedef struct {
    PyObject *LStrType;
} lstring_state;

static inline lstring_state* get_lstring_state(PyObject *module) {
    return (lstring_state*)PyModule_GetState(module);
}

// ---------- Type methods ----------
static PyObject* LStr_new(PyTypeObject *type, PyObject *args, PyObject *kwds);
static void LStr_dealloc(LStrObject *self);
static Py_hash_t LStr_hash(LStrObject *self);
static PyObject* LStr_repr(LStrObject *self);
static PyObject* LStr_add(PyObject *left, PyObject *right);
static PyObject* LStr_mul(PyObject *left, PyObject *right);
static PyObject* LStr_str(LStrObject *self);
static Py_ssize_t LStr_sq_length(PyObject *self);
static PyObject* LStr_sq_repeat(PyObject *self, Py_ssize_t count);
static PyObject* LStr_subscript(PyObject *self_obj, PyObject *key);
static PyObject* LStr_richcompare(PyObject *a, PyObject *b, int op);


// ---------- Type slots ----------
static PyType_Slot LStr_slots[] = {
    {Py_tp_new,       (void*)LStr_new},
    {Py_tp_dealloc,   (void*)LStr_dealloc},
    {Py_tp_hash,      (void*)LStr_hash},
    {Py_tp_repr,      (void*)LStr_repr},
    {Py_tp_str,       (void*)LStr_str},   // conversion to str
    {Py_tp_doc,       (void*)"lstr is a lazy string class that defers direct access to its internal buffer"},
    {Py_nb_add,       (void*)LStr_add},   // operator +
    {Py_nb_multiply,  (void*)LStr_mul},   // operator *
    {Py_tp_richcompare, (void*)LStr_richcompare},

    // Sequence protocol
    {Py_sq_length, (void*)LStr_sq_length},
    {Py_sq_concat, (void*)LStr_add},
    {Py_sq_repeat, (void*)LStr_sq_repeat},

    // lstr[index]

    // Mapping protocol: lstr[start:stop:step]
    {Py_mp_subscript, (void*)LStr_subscript},
    {0, nullptr}
};

static PyType_Spec LStr_spec = {
    "lstring.lstr",
    sizeof(LStrObject),
    0,
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,
    LStr_slots
};

// ---------- Implementation ----------
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

    try {
        switch (PyUnicode_KIND(py_str)) {
            case PyUnicode_1BYTE_KIND:
                self->buffer = new Str8Buffer(py_str);
                break;
            case PyUnicode_2BYTE_KIND:
                self->buffer = new Str16Buffer(py_str);
                break;
            case PyUnicode_4BYTE_KIND:
                self->buffer = new Str32Buffer(py_str);
                break;
            default:
                Py_DECREF((PyObject*)self);
                PyErr_SetString(PyExc_RuntimeError, "Unsupported Unicode kind");
                return nullptr;
        }
    } catch (const std::exception &e) {
        Py_DECREF((PyObject*)self);
        PyErr_SetString(PyExc_RuntimeError, e.what());
        return nullptr;
    } catch (...) {
        Py_DECREF((PyObject*)self);
        PyErr_SetString(PyExc_RuntimeError, "Buffer allocation failed");
        return nullptr;
    }

    return (PyObject*)self;
}

static void LStr_dealloc(LStrObject *self) {
    delete self->buffer;
    self->buffer = nullptr;
    Py_TYPE(self)->tp_free((PyObject*)self);
}

static Py_hash_t LStr_hash(LStrObject *self) {
    if (!self->buffer) {
        PyErr_SetString(PyExc_RuntimeError, "lstr has no buffer");
        return -1;
    }
    return self->buffer->hash();
}

static PyObject* LStr_repr(LStrObject *self) {
    if (!self->buffer) {
        PyErr_SetString(PyExc_RuntimeError, "lstr has no buffer");
        return nullptr;
    }

    return self->buffer->repr();
}

// sq_length: len(lstr)
static Py_ssize_t LStr_sq_length(PyObject *self) {
    return ((LStrObject*)self)->buffer->length();
}

// ---------- Slicing via mapping (mp_subscript) ----------
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

    try {
        if (step == 1) {
            result->buffer = new Slice1Buffer(self_obj, start, end);
        } else {
            result->buffer = new SliceBuffer(self_obj, start, end, step);
        }
    } catch (const std::exception &e) {
        Py_DECREF((PyObject*)result);
        PyErr_SetString(PyExc_RuntimeError, e.what());
        return nullptr;
    } catch (...) {
        Py_DECREF((PyObject*)result);
        PyErr_SetString(PyExc_RuntimeError, "slice creation failed");
        return nullptr;
    }

    return (PyObject*)result;
}

// ---------- Concatenation (operator +) ----------
static PyObject* LStr_add(PyObject *left, PyObject *right) {
    // Ensure both operands are of type lstr
    if (Py_TYPE(left) != Py_TYPE(right)) {
        PyErr_SetString(PyExc_TypeError, "both operands must be lstr");
        return nullptr;
    }

    PyTypeObject *type = Py_TYPE(left);
    LStrObject *self = (LStrObject*)type->tp_alloc(type, 0);
    if (!self) return nullptr;

    try {
        self->buffer = new JoinBuffer(left, right);
    } catch (const std::exception &e) {
        Py_DECREF((PyObject*)self);
        PyErr_SetString(PyExc_RuntimeError, e.what());
        return nullptr;
    } catch (...) {
        Py_DECREF((PyObject*)self);
        PyErr_SetString(PyExc_RuntimeError, "JoinBuffer allocation failed");
        return nullptr;
    }

    return (PyObject*)self;
}

// Wrap Py_ssize_t count into PyLong and reuse LStr_mul
static PyObject* LStr_sq_repeat(PyObject *self, Py_ssize_t count) {
    PyObject *count_obj = PyLong_FromSsize_t(count);
    if (!count_obj) return nullptr;
    PyObject *res = LStr_mul(self, count_obj);
    Py_DECREF(count_obj);
    return res;
}

// ---------- Multiplication (operator *) ----------
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

    try {
        result->buffer = new MulBuffer(lstr_obj, repeat_count);
    } catch (const std::exception &e) {
        Py_DECREF((PyObject*)result);
        PyErr_SetString(PyExc_RuntimeError, e.what());
        return nullptr;
    } catch (...) {
        Py_DECREF((PyObject*)result);
        PyErr_SetString(PyExc_RuntimeError, "lstr multiplication failed");
        return nullptr;
    }

    return (PyObject*)result;
}

// ---------- Compare ----------
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
static PyObject* LStr_str(LStrObject *self) {
    Buffer *buf = self->buffer;
    if (!buf) {
        PyErr_SetString(PyExc_RuntimeError, "lstr has no buffer");
        return nullptr;
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
static PyMethodDef lstring_methods[] = {
    {nullptr, nullptr, 0, nullptr}
};

// ---------- GC support ----------
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

// ---------- Multi-phase init ----------
static int lstring_mod_exec(PyObject *module) {
    lstring_state *st = get_lstring_state(module);
    PyObject *type_obj = PyType_FromSpec(&LStr_spec);
    if (!type_obj) return -1;
    st->LStrType = type_obj;
    if (PyModule_AddObject(module, "lstr", st->LStrType) < 0) {
        Py_CLEAR(st->LStrType);
        return -1;
    }
    return 0;
}

static PyModuleDef_Slot lstring_slots[] = {
    {Py_mod_exec,   (void*)lstring_mod_exec},
    {0, nullptr}
};

static struct PyModuleDef lstring_def = {
    PyModuleDef_HEAD_INIT,
    "lstring",
    "Module providing lazy string class 'lstr' for deferred buffer access",
    sizeof(lstring_state),
    lstring_methods,
    lstring_slots,
    lstring_traverse,
    lstring_clear,
    lstring_free
};

// ---------- Entry point ----------
PyMODINIT_FUNC PyInit_lstring(void) {
    return PyModuleDef_Init(&lstring_def);
}
