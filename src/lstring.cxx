/**
 * @file lstring.cxx
 * @brief Python C++ extension defining lstring.L - a lazy string class.
 */

#include <Python.h>
#include <cstdio>

#include "_lstring.hxx"
#include "lstring_utils.hxx"
#include "lstring/lstring.hxx"
#include "str_buffer.hxx"
#include "join_buffer.hxx"
#include "mul_buffer.hxx"
#include "slice_buffer.hxx"
#include "tptr.hxx"

/* Forward declarations of L type methods. */
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

/* Iterator object for L */
struct LStrIterObject {
    PyObject_HEAD
    LStrObject *source; /* borrowed but owned reference */
    Py_ssize_t index;
    Py_ssize_t length;
};

/**
 * @brief Type slots for `L` used to create the heap type from spec.
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
    {Py_tp_doc,       (void*)"L is a lazy string class that defers direct access to its internal buffer"},
    {Py_nb_add,       (void*)LStr_add},
    {Py_nb_multiply,  (void*)LStr_mul},
    {Py_tp_richcompare, (void*)LStr_richcompare},

    {Py_sq_length, (void*)LStr_sq_length},
    {Py_mp_subscript, (void*)LStr_subscript},
    {0, nullptr}
};

/**
 * @brief PyType_Spec for the `L` heap type.
 *
 * Create a concrete type object for `L` from this spec.
 */
PyType_Spec LStr_spec = {
    "_lstring.L",
    sizeof(LStrObject),
    0,
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,
    LStr_slots
};

/**
 * @brief __new__ implementation for `L`.
 *
 * Expects a single Python str argument and creates a new `L` instance
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
    // L instance from a Python str.
    PyObject *obj = make_lstr_from_pystr(type, py_str);
    return obj;
}

/**
 * @brief Deallocator for `L` instances.
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
 * @brief Hash function for `L`.
 *
 * Delegates to the underlying Buffer's cached hash implementation.
 */
static Py_hash_t LStr_hash(LStrObject *self) {
    if (!self->buffer) {
        PyErr_SetString(PyExc_RuntimeError, "L has no buffer");
        return -1;
    }
    return self->buffer->hash();
}

/**
 * @brief Sequence protocol length for `L`.
 *
 * Returns the number of code points in the underlying buffer.
 */
static Py_ssize_t LStr_sq_length(PyObject *self) {
    return ((LStrObject*)self)->buffer->length();
}

/**
 * @brief repr(self) implementation for `L`.
 *
 * Produces a Python string representing the L; delegates to Buffer::repr.
 */
static PyObject* LStr_repr(LStrObject *self) {
    if (!self->buffer) {
        PyErr_SetString(PyExc_RuntimeError, "L has no buffer");
        return nullptr;
    }

    return self->buffer->repr();
}

/**
 * @brief Support for indexing and slicing (`obj[index]` / `obj[start:stop:step]`).
 *
 * Returns a newly allocated `str` for single-index lookups and a new
 * `L` instance for slices.
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
            PyErr_SetString(PyExc_IndexError, "L index out of range");
            return nullptr;
        }
        return PyUnicode_FromOrdinal(self->buffer->value(index));
    }

    if (!PySlice_Check(key)) {
        PyErr_SetString(PyExc_TypeError, "L index type not supported");
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
    tptr<LStrObject> result(type->tp_alloc(type, 0));
    if (!result) return nullptr;

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
    lstr_optimize(result.get());

    return result.ptr().release();
}

/**
 * @brief Numeric add handler for `L`.
 *
 * Supports `L + L` and mixed `L + str` / `str + L` where
 * a Python `str` operand is wrapped into a temporary `L` backed by a
 * StrBuffer.
 */
static PyObject* LStr_add(PyObject *left, PyObject *right) {
    // Allow mixing `L` and Python `str`.
    bool left_is_str = PyUnicode_Check(left);
    bool right_is_str = PyUnicode_Check(right);    

    // Reject str+str
    if (left_is_str && right_is_str) {
        PyErr_SetString(PyExc_TypeError, "both operands cannot be Python str");
        return nullptr;
    }

    // Determine L type and validate operands. If one operand is a Python
    // str, the other must be an L. Otherwise both operands must be compatible
    // L types (same type or one is a subclass of the other). For unsupported
    // combos, return a clear error that includes the Python-level type names.
    PyTypeObject *type = nullptr;
    if (!left_is_str && !right_is_str) {
        PyTypeObject *left_type = Py_TYPE(left);
        PyTypeObject *right_type = Py_TYPE(right);
        
        // Check if types are compatible (same or one is subclass of the other)
        if (left_type != right_type && 
            !PyType_IsSubtype(left_type, right_type) && 
            !PyType_IsSubtype(right_type, left_type)) {
            // Types are incompatible
            PyErr_Format(PyExc_TypeError, "Operation %R + %R not supported", left_type, right_type);
            return nullptr;
        }
        
        // Use the more specific type (subclass) for the result
        if (PyType_IsSubtype(left_type, right_type)) {
            type = left_type;  // left is subclass of right (or same)
        } else {
            type = right_type;  // right is subclass of left
        }
    } else if (left_is_str) {
        type = Py_TYPE(right);
    } else {
        type = Py_TYPE(left);
    }
    tptr<LStrObject> left_owner, right_owner;
    if(left_is_str) {
        left_owner = tptr<LStrObject>(make_lstr_from_pystr(type, left));
        if (!left_owner) return nullptr;
        right_owner = tptr<LStrObject>(right, true);
    } else if(right_is_str) {
        right_owner = tptr<LStrObject>(make_lstr_from_pystr(type, right));
        if (!right_owner) return nullptr;
        left_owner = tptr<LStrObject>(left, true);
    } else {
        left_owner = tptr<LStrObject>(left, true);
        right_owner = tptr<LStrObject>(right, true);
    }

    // Allocate result object of the L type
    tptr<LStrObject> result(type->tp_alloc(type, 0));
    if (!result) return nullptr;

    try {
        result->buffer = new JoinBuffer(left_owner.ptr().get(), right_owner.ptr().get());
    } catch (const std::exception &e) {
        PyErr_SetString(PyExc_RuntimeError, e.what());
        return nullptr;
    } catch (...) {
        PyErr_SetString(PyExc_RuntimeError, "JoinBuffer allocation failed");
        return nullptr;
    }

    // Try to optimize/collapse small results
    lstr_optimize(result.get());

    return result.ptr().release();
}

/**
 * @brief Numeric multiply (repeat) handler for `L`.
 *
 * Supports `L * int` and `int * L`.
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
                        "L multiplication requires an integer operand");
        return nullptr;
    }

    // Convert directly to Py_ssize_t
    Py_ssize_t repeat_count = PyLong_AsSsize_t(count_obj);
    if (repeat_count == -1 && PyErr_Occurred()) {
        return nullptr;
    }
    if (repeat_count < 0) {
        PyErr_SetString(PyExc_RuntimeError,
                        "L repeat count must be non-negative");
        return nullptr;
    }

    // Allocate result
    PyTypeObject *type = Py_TYPE(lstr_obj);
    tptr<LStrObject> result(type->tp_alloc(type, 0));
    if (!result) return nullptr;

    try {
        result->buffer = new MulBuffer(lstr_obj, repeat_count);
    } catch (const std::exception &e) {
        PyErr_SetString(PyExc_RuntimeError, e.what());
        return nullptr;
    } catch (...) {
        PyErr_SetString(PyExc_RuntimeError, "L multiplication failed");
        return nullptr;
    }

    // Try to optimize/collapse small results
    lstr_optimize(result.get());

    return result.ptr().release();
}

/**
 * @brief Rich comparison implementation for `L` instances.
 *
 * Implements equality/ordering by delegating to the underlying Buffer
 * comparison. For EQ/NE a cheap hash comparison is attempted first.
 * Comparison with str types is handled at Python level.
 */
static PyObject* LStr_richcompare(PyObject *a, PyObject *b, int op) {
    // Check if both are L instances (including subclasses)
    // Find the base _lstring.L type by walking up from type_a
    PyTypeObject *type_a = Py_TYPE(a);
    PyTypeObject *base_type = type_a;
    while (base_type->tp_base != nullptr && 
           strcmp(base_type->tp_name, "_lstring.L") != 0) {
        base_type = base_type->tp_base;
    }
    
    // Check if b is also an instance of the base L type
    if (PyObject_IsInstance(b, (PyObject*)base_type) != 1) {
        Py_RETURN_NOTIMPLEMENTED;
    }
    
    LStrObject *la = (LStrObject*)a;
    LStrObject *lb = (LStrObject*)b;
    Buffer *ba = la->buffer;
    Buffer *bb = lb->buffer;

    if (!ba || !bb) {
        PyErr_SetString(PyExc_RuntimeError, "L has no buffer");
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
 * Iterator implementation for `L`.
 *
 * The iterator holds an owned reference to the source `L` object so
 * that the underlying buffer remains valid during iteration. The iterator
 * type is created on-demand via PyType_FromSpec and cached as an attribute
 * on the `L` heap type object (no global/static variables are used).
 */

static void LStrIter_dealloc(PyObject *it_obj) {
    LStrIterObject *it = (LStrIterObject*)it_obj;
    if (it->source) {
        cppy::decref(it->source);
        it->source = nullptr;
    }
    PyTypeObject *tp = Py_TYPE(it_obj);
    tp->tp_free(it_obj);
}

static PyObject* LStrIter_iternext(PyObject *it_obj) {
    LStrIterObject *it = (LStrIterObject*)it_obj;
    if (!it->source) {
        PyErr_SetString(PyExc_RuntimeError, "invalid L iterator");
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
    {Py_tp_doc, (void*)"Iterator over L yielding single-character str objects."},
    {0, nullptr}
};

PyType_Spec LStrIter_spec = {
    "_lstring._lstr_iterator",
    sizeof(LStrIterObject),
    0,
    Py_TPFLAGS_DEFAULT,
    LStrIter_slots
};

static PyObject* LStr_iter(PyObject *self) {
    PyTypeObject *lstr_type = Py_TYPE(self);

    // Try to get cached iterator type from the L type object
    tptr<PyTypeObject> it_type(PyObject_GetAttrString((PyObject*)lstr_type, "_iterator_type"));
    if (!it_type) {
        PyErr_Clear();

        it_type = tptr<PyTypeObject>(PyType_FromSpec(&LStrIter_spec));
        if (!it_type) return nullptr;

        // Cache iterator type on the L heap type object for reuse.
        if (PyObject_SetAttrString((PyObject*)lstr_type, "_iterator_type", it_type.ptr().get()) < 0) {
            return nullptr;
        }
    }

    // Create a new iterator instance
    tptr<LStrIterObject> it_obj(PyObject_CallObject(it_type.ptr().get(), nullptr));
    if (!it_obj) return nullptr;

    // Iterator holds an owned reference to the source object to keep it alive
    it_obj->source = (LStrObject*)cppy::incref(self);
    it_obj->index = 0;
    it_obj->length = it_obj->source->buffer->length();

    return it_obj.ptr().release();
}

/**
 * @brief Materialize the `L` as a concrete Python `str`.
 *
 * Delegates to buffer_to_pystr which handles both the StrBuffer shortcut
 * and materialization of lazy buffers.
 */
static PyObject* LStr_str(LStrObject *self) {
    if (!self->buffer) {
        PyErr_SetString(PyExc_RuntimeError, "L has no buffer");
        return nullptr;
    }

    return buffer_to_pystr(self->buffer);
}
