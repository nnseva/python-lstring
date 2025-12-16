/**
 * @file lstring.cxx
 * @brief Python C++ extension defining lstring._lstr - a lazy string class.
 */

#include <Python.h>
#include <cstdio>

#include "lstring.hxx"
#include "lstring_utils.hxx"
#include "buffer.hxx"
#include "str_buffer.hxx"
#include "join_buffer.hxx"
#include "mul_buffer.hxx"
#include "slice_buffer.hxx"

/* Forward declarations of lstr type methods. */
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
static PyObject* LStr_iter(PyObject *self);
static void LStrIter_dealloc(PyObject *it_obj);
static PyObject* LStrIter_iternext(PyObject *it_obj);

/* Iterator object for _lstr */
struct LStrIterObject {
    PyObject_HEAD
    LStrObject *source; /* borrowed but owned reference */
    Py_ssize_t index;
    Py_ssize_t length;
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
    {Py_tp_str,       (void*)LStr_str},
    {Py_tp_iter,      (void*)LStr_iter},
    {Py_tp_methods,   (void*)LStr_methods},
    {Py_tp_doc,       (void*)"_lstr is a lazy string class that defers direct access to its internal buffer"},
    {Py_nb_add,       (void*)LStr_add},
    {Py_nb_multiply,  (void*)LStr_mul},
    {Py_tp_richcompare, (void*)LStr_richcompare},

    {Py_sq_length, (void*)LStr_sq_length},
    {Py_mp_subscript, (void*)LStr_subscript},
    {0, nullptr}
};

/**
 * @brief PyType_Spec for the `_lstr` heap type.
 *
 * Create a concrete type object for `_lstr` from this spec.
 */
PyType_Spec LStr_spec = {
    "lstring._lstr",
    sizeof(LStrObject),
    0,
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,
    LStr_slots
};

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

    // Delegate allocation+initialization to helper that constructs an
    // _lstr instance from a Python str.
    PyObject *obj = make_lstr_from_pystr(type, py_str);
    return obj;
}

/**
 * @brief Deallocator for `_lstr` instances.
 *
 * Frees the internal Buffer and releases the object memory.
 */
static void LStr_dealloc(LStrObject *self) {
    if (self->buffer) {
        delete self->buffer;
        self->buffer = nullptr;
    }
    Py_TYPE(self)->tp_free((PyObject*)self);
}

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
        PyObject *new_left = make_lstr_from_pystr(type, left);
        if (!new_left) return nullptr;
        left_owner = cppy::ptr(new_left);
        right_owner = cppy::ptr(right, true);
    } else if(right_is_str) {
        PyObject *new_right = make_lstr_from_pystr(type, right);
        if (!new_right) return nullptr;
        right_owner = cppy::ptr(new_right);
        left_owner = cppy::ptr(left, true);
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

/**
 * Iterator implementation for `_lstr`.
 *
 * The iterator holds an owned reference to the source `_lstr` object so
 * that the underlying buffer remains valid during iteration. The iterator
 * type is created on-demand via PyType_FromSpec and cached as an attribute
 * on the `_lstr` heap type object (no global/static variables are used).
 */

static void LStrIter_dealloc(PyObject *it_obj) {
    LStrIterObject *it = (LStrIterObject*)it_obj;
    if (it->source) {
        Py_DECREF((PyObject*)it->source);
        it->source = nullptr;
    }
    PyTypeObject *tp = Py_TYPE(it_obj);
    tp->tp_free(it_obj);
}

static PyObject* LStrIter_iternext(PyObject *it_obj) {
    LStrIterObject *it = (LStrIterObject*)it_obj;
    if (!it->source) {
        PyErr_SetString(PyExc_RuntimeError, "invalid lstr iterator");
        return nullptr;
    }
    if (it->index >= it->length) {
        PyErr_SetNone(PyExc_StopIteration);
        return nullptr;
    }
    uint32_t ch = it->source->buffer->value(it->index);
    it->index += 1;
    return PyUnicode_FromOrdinal(ch);
}

PyType_Slot LStrIter_slots[] = {
    {Py_tp_dealloc, (void*)LStrIter_dealloc},
    {Py_tp_iternext, (void*)LStrIter_iternext},
    {Py_tp_iter, (void*)PyObject_SelfIter},
    {Py_tp_doc, (void*)"Iterator over _lstr yielding single-character str objects."},
    {0, nullptr}
};

PyType_Spec LStrIter_spec = {
    "lstring._lstr_iterator",
    sizeof(LStrIterObject),
    0,
    Py_TPFLAGS_DEFAULT,
    LStrIter_slots
};

static PyObject* LStr_iter(PyObject *self) {
    PyTypeObject *lstr_type = Py_TYPE(self);

    // Try to get cached iterator type from the lstr type object
    PyObject *it_type = PyObject_GetAttrString((PyObject*)lstr_type, "_iterator_type");
    if (!it_type) {
        PyErr_Clear();

        it_type = PyType_FromSpec(&LStrIter_spec);
        if (!it_type) return nullptr;

        // Cache iterator type on the lstr heap type object for reuse.
        if (PyObject_SetAttrString((PyObject*)lstr_type, "_iterator_type", it_type) < 0) {
            Py_DECREF(it_type);
            return nullptr;
        }
    }

    // Create a new iterator instance
    PyObject *it_obj = PyObject_CallObject(it_type, nullptr);
    if (!it_obj) return nullptr;

    LStrIterObject *it = (LStrIterObject*)it_obj;
    Py_INCREF(self);
    it->source = (LStrObject*)self;
    it->index = 0;
    it->length = it->source->buffer->length();

    return it_obj;
}

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
