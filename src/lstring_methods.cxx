/**
 * @file lstring_methods.cxx
 * @brief Method implementations and method table for `L`.
 */

#include <Python.h>
#include "lstring.hxx"
#include "lstring_utils.hxx"
#include "buffer.hxx"
#include "str_buffer.hxx"
#include "tptr.hxx"

static PyObject* LStr_collapse(LStrObject *self, PyObject *Py_UNUSED(ignored));
static PyObject* LStr_optimize(LStrObject *self, PyObject *Py_UNUSED(ignored));
static PyObject* LStr_find(LStrObject *self, PyObject *args, PyObject *kwds);
static PyObject* LStr_rfind(LStrObject *self, PyObject *args, PyObject *kwds);
static PyObject* LStr_findc(LStrObject *self, PyObject *args, PyObject *kwds);
static PyObject* LStr_rfindc(LStrObject *self, PyObject *args, PyObject *kwds);
static PyObject* LStr_findcs(LStrObject *self, PyObject *args, PyObject *kwds);
static PyObject* LStr_rfindcs(LStrObject *self, PyObject *args, PyObject *kwds);
static PyObject* LStr_findcc(LStrObject *self, PyObject *args, PyObject *kwds);
static PyObject* LStr_rfindcc(LStrObject *self, PyObject *args, PyObject *kwds);

// Character classification methods
static PyObject* LStr_isspace(LStrObject *self, PyObject *Py_UNUSED(ignored));
static PyObject* LStr_isalpha(LStrObject *self, PyObject *Py_UNUSED(ignored));
static PyObject* LStr_isdigit(LStrObject *self, PyObject *Py_UNUSED(ignored));
static PyObject* LStr_isalnum(LStrObject *self, PyObject *Py_UNUSED(ignored));
static PyObject* LStr_isupper(LStrObject *self, PyObject *Py_UNUSED(ignored));
static PyObject* LStr_islower(LStrObject *self, PyObject *Py_UNUSED(ignored));
static PyObject* LStr_isdecimal(LStrObject *self, PyObject *Py_UNUSED(ignored));
static PyObject* LStr_isnumeric(LStrObject *self, PyObject *Py_UNUSED(ignored));
static PyObject* LStr_isprintable(LStrObject *self, PyObject *Py_UNUSED(ignored));
static PyObject* LStr_istitle(LStrObject *self, PyObject *Py_UNUSED(ignored));

/**
 * @brief Method table for the L type.
 *
 * Contains Python-callable methods exposed on the `L` type. Each entry
 * maps a method name to a C function and calling convention.
 */
PyMethodDef LStr_methods[] = {
    {"collapse", (PyCFunction)LStr_collapse, METH_NOARGS, "Collapse internal buffer to a contiguous str buffer"},
    {"optimize", (PyCFunction)LStr_optimize, METH_NOARGS, "Optimize internal buffer based on threshold"},
    {"find", (PyCFunction)LStr_find, METH_VARARGS | METH_KEYWORDS, "Find substring like str.find(sub, start=None, end=None)"},
    {"rfind", (PyCFunction)LStr_rfind, METH_VARARGS | METH_KEYWORDS, "Find last occurrence like str.rfind(sub, start=None, end=None)"},
    {"findc", (PyCFunction)LStr_findc, METH_VARARGS | METH_KEYWORDS, "Find single code point: findc(ch, start=None, end=None)"},
    {"rfindc", (PyCFunction)LStr_rfindc, METH_VARARGS | METH_KEYWORDS, "Find single code point from right: rfindc(ch, start=None, end=None)"},
    {"findcs", (PyCFunction)LStr_findcs, METH_VARARGS | METH_KEYWORDS, "Find any character from set: findcs(charset, start=None, end=None)"},
    {"rfindcs", (PyCFunction)LStr_rfindcs, METH_VARARGS | METH_KEYWORDS, "Find any character from set from right: rfindcs(charset, start=None, end=None)"},
    {"findcc", (PyCFunction)LStr_findcc, METH_VARARGS | METH_KEYWORDS, "Find character by class: findcc(class_mask, start=None, end=None, invert=False)"},
    {"rfindcc", (PyCFunction)LStr_rfindcc, METH_VARARGS | METH_KEYWORDS, "Find character by class from right: rfindcc(class_mask, start=None, end=None, invert=False)"},
    {"isspace", (PyCFunction)LStr_isspace, METH_NOARGS, "Return True if all characters are whitespace, False otherwise"},
    {"isalpha", (PyCFunction)LStr_isalpha, METH_NOARGS, "Return True if all characters are alphabetic, False otherwise"},
    {"isdigit", (PyCFunction)LStr_isdigit, METH_NOARGS, "Return True if all characters are digits, False otherwise"},
    {"isalnum", (PyCFunction)LStr_isalnum, METH_NOARGS, "Return True if all characters are alphanumeric, False otherwise"},
    {"isupper", (PyCFunction)LStr_isupper, METH_NOARGS, "Return True if all cased characters are uppercase, False otherwise"},
    {"islower", (PyCFunction)LStr_islower, METH_NOARGS, "Return True if all cased characters are lowercase, False otherwise"},
    {"isdecimal", (PyCFunction)LStr_isdecimal, METH_NOARGS, "Return True if all characters are decimal digits, False otherwise"},
    {"isnumeric", (PyCFunction)LStr_isnumeric, METH_NOARGS, "Return True if all characters are numeric, False otherwise"},
    {"isprintable", (PyCFunction)LStr_isprintable, METH_NOARGS, "Return True if all characters are printable, False otherwise"},
    {"istitle", (PyCFunction)LStr_istitle, METH_NOARGS, "Return True if the string is titlecased, False otherwise"},
    {nullptr, nullptr, 0, nullptr}
};


/**
 * @brief Find method: search for a substring in the L.
 *
 * Signature: find(self, sub, start=None, end=None)
 * Accepts `sub` as either a Python str or another L. Negative start/end
 * are interpreted as offsets from the end (slice semantics). Returns the
 * lowest index where sub is found, or -1 if not found.
 */
static PyObject* LStr_find(LStrObject *self, PyObject *args, PyObject *kwds) {
    static char *kwlist[] = {(char*)"sub", (char*)"start", (char*)"end", nullptr};
    PyObject *sub_obj = nullptr;
    PyObject *start_obj = Py_None;
    PyObject *end_obj = Py_None;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O|OO:find", kwlist,
                                     &sub_obj, &start_obj, &end_obj)) {
        return nullptr;
    }

    // Validate source buffer
    if (!self || !self->buffer) {
        PyErr_SetString(PyExc_RuntimeError, "invalid L object");
        return nullptr;
    }
    Buffer *src = self->buffer;
    Py_ssize_t src_len = (Py_ssize_t)src->length();

    // Obtain a Buffer for sub: accept Python str or L
    tptr<LStrObject> sub_owner;
    if (PyUnicode_Check(sub_obj)) {
        // wrap Python str into a temporary `L` via factory and own it
        PyTypeObject *type = Py_TYPE(self);
        sub_owner = tptr<LStrObject>(make_lstr_from_pystr(type, sub_obj));
        if (!sub_owner) return nullptr;
    } else if (PyObject_HasAttrString((PyObject*)Py_TYPE(sub_obj), "collapse")) {
        // assume it's an L-like object
        LStrObject *lsub = (LStrObject*)sub_obj;
        if (!lsub->buffer) {
            PyErr_SetString(PyExc_RuntimeError, "substring L has no buffer");
            return nullptr;
        }
        sub_owner = tptr<LStrObject>(sub_obj, true);
    } else {
        PyErr_SetString(PyExc_TypeError, "sub must be str or L");
        return nullptr;
    }

    Py_ssize_t sub_len = (Py_ssize_t)sub_owner->buffer->length();

    // Parse start
    Py_ssize_t start;
    if (start_obj == Py_None) {
        start = 0;
    } else {
        if (!PyLong_Check(start_obj)) {
            PyErr_SetString(PyExc_TypeError, "start/end must be int or None");
            return nullptr;
        }
        start = PyLong_AsSsize_t(start_obj);
        if (start == -1 && PyErr_Occurred()) return nullptr;
        if (start < 0) start += src_len;
    }

    // Parse end
    Py_ssize_t end;
    if (end_obj == Py_None) {
        end = src_len;
    } else {
        if (!PyLong_Check(end_obj)) {
            PyErr_SetString(PyExc_TypeError, "start/end must be int or None");
            return nullptr;
        }
        end = PyLong_AsSsize_t(end_obj);
        if (end == -1 && PyErr_Occurred()) return nullptr;
        if (end < 0) end += src_len;
    }

    // Clamp start/end per Python semantics
    if (start < 0) start = 0;
    if (end < 0) end = 0;
    if (start > src_len) {
        // start beyond end -> not found
        return PyLong_FromLong(-1);
    }
    if (end > src_len) end = src_len;

    // Empty substring is found at start if start<=len, but if start==len
    // it's allowed (empty at end). If start > len we already returned -1.
    if (sub_len == 0) {
        return PyLong_FromSsize_t(start);
    }

    // If the remaining region is shorter than sub, not found
    if (end - start < sub_len) {
        return PyLong_FromLong(-1);
    }

    // Fast-path: if both source and substring are string-backed buffers,
    // delegate to the built-in Python unicode find implementation which is
    // optimized in C and understands Python slice semantics.
    if (src->is_str() && sub_owner->buffer->is_str()) {
        PyObject *src_py = ((StrBuffer*)src)->get_str();
        PyObject *sub_py = ((StrBuffer*)sub_owner->buffer)->get_str();
        Py_ssize_t idx = PyUnicode_Find(src_py, sub_py, start, end, 1); // direction=1 -> find
        if (idx == -1 && PyErr_Occurred()) return nullptr;
        return PyLong_FromSsize_t(idx);
    }

    // Optimized scan: find occurrences of the first code point of `sub`
    // and only perform the full element-wise comparison at those
    // candidate positions. This delegates single-codepoint search to
    // the buffer implementation which may provide faster paths for
    // joined/repeated/sliced buffers.
    uint32_t first_cp = sub_owner->buffer->value(0);
    Py_ssize_t pos = start;
    Py_ssize_t last = end - sub_len;
    while (pos <= last) {
        // find next occurrence of first_cp in [pos, end)
        Py_ssize_t i = src->findc(pos, end, first_cp);
        if (i < 0 || i > last) break; // not found or not enough room for full match

        // verify full substring match at position i
        // We can skip j==0 because findc returned i where
        // src->value(i) == first_cp == sub_owner->buffer->value(0).
        bool match = true;
        for (Py_ssize_t j = 1; j < sub_len; ++j) {
            uint32_t a = src->value(i + j);
            uint32_t b = sub_owner->buffer->value(j);
            if (a != b) { match = false; break; }
        }
        if (match) return PyLong_FromSsize_t(i);

        // advance to the next possible position after the found cp
        pos = i + 1;
    }

    return PyLong_FromLong(-1);
}


/**
 * @brief rfind(self, sub, start=None, end=None)
 *
 * Mirrors semantics of str.rfind: returns highest index where sub is
 * found in the slice [start:end], or -1 if not found.
 */
static PyObject* LStr_rfind(LStrObject *self, PyObject *args, PyObject *kwds) {
    static char *kwlist[] = {(char*)"sub", (char*)"start", (char*)"end", nullptr};
    PyObject *sub_obj = nullptr;
    PyObject *start_obj = Py_None;
    PyObject *end_obj = Py_None;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O|OO:rfind", kwlist,
                                     &sub_obj, &start_obj, &end_obj)) {
        return nullptr;
    }

    if (!self || !self->buffer) {
        PyErr_SetString(PyExc_RuntimeError, "invalid L object");
        return nullptr;
    }
    Buffer *src = self->buffer;
    Py_ssize_t src_len = (Py_ssize_t)src->length();

    // Obtain sub buffer (str or L)
    tptr<LStrObject> sub_owner;
    if (PyUnicode_Check(sub_obj)) {
        PyTypeObject *type = Py_TYPE(self);
        sub_owner = tptr<LStrObject>(make_lstr_from_pystr(type, sub_obj));
        if (!sub_owner) return nullptr;
    } else if (PyObject_HasAttrString((PyObject*)Py_TYPE(sub_obj), "collapse")) {
        LStrObject *lsub = (LStrObject*)sub_obj;
        if (!lsub->buffer) {
            PyErr_SetString(PyExc_RuntimeError, "substring L has no buffer");
            return nullptr;
        }
        sub_owner = tptr<LStrObject>(sub_obj, true);
    } else {
        PyErr_SetString(PyExc_TypeError, "sub must be str or L");
        return nullptr;
    }

    Py_ssize_t sub_len = (Py_ssize_t)sub_owner->buffer->length();

    // Parse start
    Py_ssize_t start;
    if (start_obj == Py_None) {
        start = 0;
    } else {
        if (!PyLong_Check(start_obj)) {
            PyErr_SetString(PyExc_TypeError, "start/end must be int or None");
            return nullptr;
        }
        start = PyLong_AsSsize_t(start_obj);
        if (start == -1 && PyErr_Occurred()) return nullptr;
        if (start < 0) start += src_len;
    }

    // Parse end
    Py_ssize_t end;
    if (end_obj == Py_None) {
        end = src_len;
    } else {
        if (!PyLong_Check(end_obj)) {
            PyErr_SetString(PyExc_TypeError, "start/end must be int or None");
            return nullptr;
        }
        end = PyLong_AsSsize_t(end_obj);
        if (end == -1 && PyErr_Occurred()) return nullptr;
        if (end < 0) end += src_len;
    }

    // Clamp start/end per Python semantics
    if (start < 0) start = 0;
    if (end < 0) end = 0;
    if (start > src_len) {
        // start beyond end -> not found
        return PyLong_FromLong(-1);
    }
    if (end > src_len) end = src_len;

    // Empty substring behavior: return end if sub_len == 0 (rfind rules)
    if (sub_len == 0) {
        // For rfind, empty substring is found at min(end, src_len)
        Py_ssize_t pos = end;
        if (pos > src_len) pos = src_len;
        return PyLong_FromSsize_t(pos);
    }

    // If remaining region is shorter than sub, not found
    if (end - start < sub_len) {
        return PyLong_FromLong(-1);
    }

    // Fast-path: if both source and substring are string-backed buffers,
    // delegate to Python unicode rfind via PyUnicode_Find with direction=-1.
    if (src->is_str() && sub_owner->buffer->is_str()) {
        PyObject *src_py = ((StrBuffer*)src)->get_str();
        PyObject *sub_py = ((StrBuffer*)sub_owner->buffer)->get_str();
        Py_ssize_t idx = PyUnicode_Find(src_py, sub_py, start, end, -1); // direction=-1 -> rfind
        if (idx == -1 && PyErr_Occurred()) return nullptr;
        return PyLong_FromSsize_t(idx);
    }

    // Scan from the right using rfindc on the LAST code point of `sub`.
    // When rfindc returns an index `pos` where src->value(pos) == last_cp,
    // that corresponds to a candidate match last code point.
    // Verify the substring by comparing the
    // remaining code points in backward direction.
    uint32_t last_cp = sub_owner->buffer->value(sub_len - 1);
    Py_ssize_t pos = end; // rfindc searches in [start, pos)
    while (pos > start + sub_len - 1) {
        Py_ssize_t k = src->rfindc(start, pos, last_cp);
        if (k < 0) break; // no more occurrences
        if (k < start + sub_len - 1) break; // not enough room for full match

        // verify substring backward; we can skip comparing the last
        // code point because rfindc already matched it at `k`.
        bool match = true;
        for (Py_ssize_t j = 1; j < sub_len; ++j) {
            uint32_t a = src->value(k - j);
            uint32_t b = sub_owner->buffer->value(sub_len - j - 1);
            if (a != b) { match = false; break; }
        }
        if (match) return PyLong_FromSsize_t(k - sub_len + 1);
        pos = k; // continue searching earlier
    }

    return PyLong_FromLong(-1);
}


/**
 * @brief Python method wrapper: collapse(self)
 *
 * Exposes the internal `lstr_collapse` helper as a Python-callable
 * method.
 */
static PyObject* LStr_collapse(LStrObject *self, PyObject *Py_UNUSED(ignored)) {
    if (!self) {
        PyErr_SetString(PyExc_RuntimeError, "invalid L object");
        return nullptr;
    }
    lstr_collapse(self);
    if (PyErr_Occurred()) return nullptr;
    Py_RETURN_NONE;
}

/**
 * @brief Python method wrapper: optimize(self)
 *
 * Exposes the internal `lstr_optimize` helper as a Python-callable
 * method. Applies threshold-based optimization to the buffer.
 */
static PyObject* LStr_optimize(LStrObject *self, PyObject *Py_UNUSED(ignored)) {
    if (!self) {
        PyErr_SetString(PyExc_RuntimeError, "invalid L object");
        return nullptr;
    }
    lstr_optimize(self);
    if (PyErr_Occurred()) return nullptr;
    Py_RETURN_NONE;
}


/**
 * findc(self, ch, start=None, end=None)
 * Accept ch as int (code point) or a one-character str. Delegate to
 * buffer->findc with mapped indices and return slice-relative index or -1.
 */
static PyObject* LStr_findc(LStrObject *self, PyObject *args, PyObject *kwds) {
    static char *kwlist[] = {(char*)"ch", (char*)"start", (char*)"end", nullptr};
    PyObject *ch_obj = nullptr;
    PyObject *start_obj = Py_None;
    PyObject *end_obj = Py_None;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O|OO:findc", kwlist,
                                     &ch_obj, &start_obj, &end_obj)) {
        return nullptr;
    }

    if (!self || !self->buffer) {
        PyErr_SetString(PyExc_RuntimeError, "invalid L object");
        return nullptr;
    }
    Buffer *buf = self->buffer;
    Py_ssize_t buf_len = (Py_ssize_t)buf->length();

    // parse ch: accept int or 1-char str
    uint32_t ch;
    if (PyLong_Check(ch_obj)) {
        long tmp = PyLong_AsLong(ch_obj);
        if (tmp < 0) {
            PyErr_SetString(PyExc_ValueError, "ch must be a non-negative code point");
            return nullptr;
        }
        ch = (uint32_t)tmp;
    } else if (PyUnicode_Check(ch_obj)) {
        if (PyUnicode_GetLength(ch_obj) != 1) {
            PyErr_SetString(PyExc_ValueError, "ch must be a single character string");
            return nullptr;
        }
        Py_UCS4 u = PyUnicode_ReadChar(ch_obj, 0);
        ch = (uint32_t)u;
    } else {
        PyErr_SetString(PyExc_TypeError, "ch must be int or 1-char str");
        return nullptr;
    }

    // parse start/end similar to find
    Py_ssize_t start;
    if (start_obj == Py_None) {
        start = 0;
    } else {
        if (!PyLong_Check(start_obj)) { PyErr_SetString(PyExc_TypeError, "start/end must be int or None"); return nullptr; }
        start = PyLong_AsSsize_t(start_obj);
        if (start == -1 && PyErr_Occurred()) return nullptr;
        if (start < 0) start += buf_len;
    }

    Py_ssize_t end;
    if (end_obj == Py_None) {
        end = buf_len;
    } else {
        if (!PyLong_Check(end_obj)) { PyErr_SetString(PyExc_TypeError, "start/end must be int or None"); return nullptr; }
        end = PyLong_AsSsize_t(end_obj);
        if (end == -1 && PyErr_Occurred()) return nullptr;
        if (end < 0) end += buf_len;
    }

    if (start < 0) start = 0;
    if (end < 0) end = 0;
    if (start > buf_len) return PyLong_FromLong(-1);
    if (end > buf_len) end = buf_len;
    if (start >= end) return PyLong_FromLong(-1);

    Py_ssize_t res = buf->findc(start, end, ch);
    return PyLong_FromSsize_t(res);
}


/**
 * rfindc(self, ch, start=None, end=None)
 */
static PyObject* LStr_rfindc(LStrObject *self, PyObject *args, PyObject *kwds) {
    static char *kwlist[] = {(char*)"ch", (char*)"start", (char*)"end", nullptr};
    PyObject *ch_obj = nullptr;
    PyObject *start_obj = Py_None;
    PyObject *end_obj = Py_None;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O|OO:rfindc", kwlist,
                                     &ch_obj, &start_obj, &end_obj)) {
        return nullptr;
    }

    if (!self || !self->buffer) {
        PyErr_SetString(PyExc_RuntimeError, "invalid L object");
        return nullptr;
    }
    Buffer *buf = self->buffer;
    Py_ssize_t buf_len = (Py_ssize_t)buf->length();

    uint32_t ch;
    if (PyLong_Check(ch_obj)) {
        long tmp = PyLong_AsLong(ch_obj);
        if (tmp < 0) { PyErr_SetString(PyExc_ValueError, "ch must be a non-negative code point"); return nullptr; }
        ch = (uint32_t)tmp;
    } else if (PyUnicode_Check(ch_obj)) {
        if (PyUnicode_GetLength(ch_obj) != 1) { PyErr_SetString(PyExc_ValueError, "ch must be a single character string"); return nullptr; }
        Py_UCS4 u = PyUnicode_ReadChar(ch_obj, 0);
        ch = (uint32_t)u;
    } else { PyErr_SetString(PyExc_TypeError, "ch must be int or 1-char str"); return nullptr; }

    // parse start/end
    Py_ssize_t start;
    if (start_obj == Py_None) {
        start = 0;
    } else {
        if (!PyLong_Check(start_obj)) { PyErr_SetString(PyExc_TypeError, "start/end must be int or None"); return nullptr; }
        start = PyLong_AsSsize_t(start_obj);
        if (start == -1 && PyErr_Occurred()) return nullptr;
        if (start < 0) start += buf_len;
    }

    Py_ssize_t end;
    if (end_obj == Py_None) {
        end = buf_len;
    } else {
        if (!PyLong_Check(end_obj)) { PyErr_SetString(PyExc_TypeError, "start/end must be int or None"); return nullptr; }
        end = PyLong_AsSsize_t(end_obj);
        if (end == -1 && PyErr_Occurred()) return nullptr;
        if (end < 0) end += buf_len;
    }

    if (start < 0) start = 0;
    if (end < 0) end = 0;
    if (start > buf_len) return PyLong_FromLong(-1);
    if (end > buf_len) end = buf_len;
    if (start >= end) return PyLong_FromLong(-1);

    Py_ssize_t res = buf->rfindc(start, end, ch);
    return PyLong_FromSsize_t(res);
}


/**
 * @brief findcs(self, charset, start=None, end=None)
 * 
 * Find first occurrence of any character from charset.
 */
static PyObject* LStr_findcs(LStrObject *self, PyObject *args, PyObject *kwds) {
    static char *kwlist[] = {(char*)"charset", (char*)"start", (char*)"end", nullptr};
    PyObject *charset_obj = nullptr;
    PyObject *start_obj = Py_None;
    PyObject *end_obj = Py_None;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O|OO:findcs", kwlist,
                                     &charset_obj, &start_obj, &end_obj)) {
        return nullptr;
    }

    if (!self || !self->buffer) {
        PyErr_SetString(PyExc_RuntimeError, "invalid L object");
        return nullptr;
    }
    Buffer *buf = self->buffer;
    Py_ssize_t buf_len = (Py_ssize_t)buf->length();

    // Check if charset is an L instance (including subclasses)
    // Find the base _lstring.L type by walking up from self's type
    PyTypeObject *type_self = Py_TYPE(self);
    PyTypeObject *base_type = type_self;
    while (base_type->tp_base != nullptr && 
           strcmp(base_type->tp_name, "_lstring.L") != 0) {
        base_type = base_type->tp_base;
    }
    
    // Check if charset_obj is also an instance of the base L type
    if (PyObject_IsInstance(charset_obj, (PyObject*)base_type) != 1) {
        PyErr_SetString(PyExc_TypeError, "charset must be an L instance");
        return nullptr;
    }
    
    LStrObject *charset_lstr = (LStrObject*)charset_obj;
    if (!charset_lstr->buffer) {
        PyErr_SetString(PyExc_RuntimeError, "charset L has no buffer");
        return nullptr;
    }
    Buffer *charset = charset_lstr->buffer;

    // Parse start/end
    Py_ssize_t start;
    if (start_obj == Py_None) {
        start = 0;
    } else {
        if (!PyLong_Check(start_obj)) {
            PyErr_SetString(PyExc_TypeError, "start must be int or None");
            return nullptr;
        }
        start = PyLong_AsSsize_t(start_obj);
        if (start == -1 && PyErr_Occurred()) return nullptr;
        if (start < 0) start += buf_len;
    }

    Py_ssize_t end;
    if (end_obj == Py_None) {
        end = buf_len;
    } else {
        if (!PyLong_Check(end_obj)) {
            PyErr_SetString(PyExc_TypeError, "end must be int or None");
            return nullptr;
        }
        end = PyLong_AsSsize_t(end_obj);
        if (end == -1 && PyErr_Occurred()) return nullptr;
        if (end < 0) end += buf_len;
    }

    if (start < 0) start = 0;
    if (end < 0) end = 0;
    if (start > buf_len) return PyLong_FromLong(-1);
    if (end > buf_len) end = buf_len;
    if (start >= end) return PyLong_FromLong(-1);

    Py_ssize_t res = buf->findcs(start, end, charset);
    return PyLong_FromSsize_t(res);
}


/**
 * @brief rfindcs(self, charset, start=None, end=None)
 * 
 * Find last occurrence of any character from charset.
 */
static PyObject* LStr_rfindcs(LStrObject *self, PyObject *args, PyObject *kwds) {
    static char *kwlist[] = {(char*)"charset", (char*)"start", (char*)"end", nullptr};
    PyObject *charset_obj = nullptr;
    PyObject *start_obj = Py_None;
    PyObject *end_obj = Py_None;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O|OO:rfindcs", kwlist,
                                     &charset_obj, &start_obj, &end_obj)) {
        return nullptr;
    }

    if (!self || !self->buffer) {
        PyErr_SetString(PyExc_RuntimeError, "invalid L object");
        return nullptr;
    }
    Buffer *buf = self->buffer;
    Py_ssize_t buf_len = (Py_ssize_t)buf->length();

    // Check if charset is an L instance (including subclasses)
    // Find the base _lstring.L type by walking up from self's type
    PyTypeObject *type_self = Py_TYPE(self);
    PyTypeObject *base_type = type_self;
    while (base_type->tp_base != nullptr && 
           strcmp(base_type->tp_name, "_lstring.L") != 0) {
        base_type = base_type->tp_base;
    }
    
    // Check if charset_obj is also an instance of the base L type
    if (PyObject_IsInstance(charset_obj, (PyObject*)base_type) != 1) {
        PyErr_SetString(PyExc_TypeError, "charset must be an L instance");
        return nullptr;
    }
    
    LStrObject *charset_lstr = (LStrObject*)charset_obj;
    if (!charset_lstr->buffer) {
        PyErr_SetString(PyExc_RuntimeError, "charset L has no buffer");
        return nullptr;
    }
    Buffer *charset = charset_lstr->buffer;

    // Parse start/end
    Py_ssize_t start;
    if (start_obj == Py_None) {
        start = 0;
    } else {
        if (!PyLong_Check(start_obj)) {
            PyErr_SetString(PyExc_TypeError, "start must be int or None");
            return nullptr;
        }
        start = PyLong_AsSsize_t(start_obj);
        if (start == -1 && PyErr_Occurred()) return nullptr;
        if (start < 0) start += buf_len;
    }

    Py_ssize_t end;
    if (end_obj == Py_None) {
        end = buf_len;
    } else {
        if (!PyLong_Check(end_obj)) {
            PyErr_SetString(PyExc_TypeError, "end must be int or None");
            return nullptr;
        }
        end = PyLong_AsSsize_t(end_obj);
        if (end == -1 && PyErr_Occurred()) return nullptr;
        if (end < 0) end += buf_len;
    }

    if (start < 0) start = 0;
    if (end < 0) end = 0;
    if (start > buf_len) return PyLong_FromLong(-1);
    if (end > buf_len) end = buf_len;
    if (start >= end) return PyLong_FromLong(-1);

    Py_ssize_t res = buf->rfindcs(start, end, charset);
    return PyLong_FromSsize_t(res);
}


/**
 * @brief isspace() method: check if all characters are whitespace.
 */
static PyObject* LStr_isspace(LStrObject *self, PyObject *Py_UNUSED(ignored)) {
    if (!self || !self->buffer) {
        PyErr_SetString(PyExc_RuntimeError, "invalid L object");
        return nullptr;
    }
    return PyBool_FromLong(self->buffer->isspace());
}

/**
 * @brief isalpha() method: check if all characters are alphabetic.
 */
static PyObject* LStr_isalpha(LStrObject *self, PyObject *Py_UNUSED(ignored)) {
    if (!self || !self->buffer) {
        PyErr_SetString(PyExc_RuntimeError, "invalid L object");
        return nullptr;
    }
    return PyBool_FromLong(self->buffer->isalpha());
}

/**
 * @brief isdigit() method: check if all characters are digits.
 */
static PyObject* LStr_isdigit(LStrObject *self, PyObject *Py_UNUSED(ignored)) {
    if (!self || !self->buffer) {
        PyErr_SetString(PyExc_RuntimeError, "invalid L object");
        return nullptr;
    }
    return PyBool_FromLong(self->buffer->isdigit());
}

/**
 * @brief isalnum() method: check if all characters are alphanumeric.
 */
static PyObject* LStr_isalnum(LStrObject *self, PyObject *Py_UNUSED(ignored)) {
    if (!self || !self->buffer) {
        PyErr_SetString(PyExc_RuntimeError, "invalid L object");
        return nullptr;
    }
    return PyBool_FromLong(self->buffer->isalnum());
}

/**
 * @brief isupper() method: check if all cased characters are uppercase.
 */
static PyObject* LStr_isupper(LStrObject *self, PyObject *Py_UNUSED(ignored)) {
    if (!self || !self->buffer) {
        PyErr_SetString(PyExc_RuntimeError, "invalid L object");
        return nullptr;
    }
    return PyBool_FromLong(self->buffer->isupper());
}

/**
 * @brief islower() method: check if all cased characters are lowercase.
 */
static PyObject* LStr_islower(LStrObject *self, PyObject *Py_UNUSED(ignored)) {
    if (!self || !self->buffer) {
        PyErr_SetString(PyExc_RuntimeError, "invalid L object");
        return nullptr;
    }
    return PyBool_FromLong(self->buffer->islower());
}

/**
 * @brief isdecimal() method: check if all characters are decimal digits.
 */
static PyObject* LStr_isdecimal(LStrObject *self, PyObject *Py_UNUSED(ignored)) {
    if (!self || !self->buffer) {
        PyErr_SetString(PyExc_RuntimeError, "invalid L object");
        return nullptr;
    }
    return PyBool_FromLong(self->buffer->isdecimal());
}

/**
 * @brief isnumeric() method: check if all characters are numeric.
 */
static PyObject* LStr_isnumeric(LStrObject *self, PyObject *Py_UNUSED(ignored)) {
    if (!self || !self->buffer) {
        PyErr_SetString(PyExc_RuntimeError, "invalid L object");
        return nullptr;
    }
    return PyBool_FromLong(self->buffer->isnumeric());
}

/**
 * @brief isprintable() method: check if all characters are printable.
 */
static PyObject* LStr_isprintable(LStrObject *self, PyObject *Py_UNUSED(ignored)) {
    if (!self || !self->buffer) {
        PyErr_SetString(PyExc_RuntimeError, "invalid L object");
        return nullptr;
    }
    return PyBool_FromLong(self->buffer->isprintable());
}

/**
 * @brief istitle() method: check if the string is titlecased.
 */
static PyObject* LStr_istitle(LStrObject *self, PyObject *Py_UNUSED(ignored)) {
    if (!self || !self->buffer) {
        PyErr_SetString(PyExc_RuntimeError, "invalid L object");
        return nullptr;
    }
    return PyBool_FromLong(self->buffer->istitle());
}

/**
 * @brief findcc(self, class_mask, start=None, end=None, invert=False)
 * 
 * Find first character matching (or not matching) the specified character class(es).
 */
static PyObject* LStr_findcc(LStrObject *self, PyObject *args, PyObject *kwds) {
    static char *kwlist[] = {(char*)"class_mask", (char*)"start", (char*)"end", (char*)"invert", nullptr};
    unsigned long class_mask;
    PyObject *start_obj = Py_None;
    PyObject *end_obj = Py_None;
    int invert = 0;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "k|OOp:findcc", kwlist,
                                     &class_mask, &start_obj, &end_obj, &invert)) {
        return nullptr;
    }

    if (!self || !self->buffer) {
        PyErr_SetString(PyExc_RuntimeError, "invalid L object");
        return nullptr;
    }
    Buffer *buf = self->buffer;
    Py_ssize_t buf_len = (Py_ssize_t)buf->length();

    // Parse start/end similar to findc
    Py_ssize_t start;
    if (start_obj == Py_None) {
        start = 0;
    } else {
        if (!PyLong_Check(start_obj)) {
            PyErr_SetString(PyExc_TypeError, "start must be int or None");
            return nullptr;
        }
        start = PyLong_AsSsize_t(start_obj);
        if (start == -1 && PyErr_Occurred()) return nullptr;
        if (start < 0) start += buf_len;
    }

    Py_ssize_t end;
    if (end_obj == Py_None) {
        end = buf_len;
    } else {
        if (!PyLong_Check(end_obj)) {
            PyErr_SetString(PyExc_TypeError, "end must be int or None");
            return nullptr;
        }
        end = PyLong_AsSsize_t(end_obj);
        if (end == -1 && PyErr_Occurred()) return nullptr;
        if (end < 0) end += buf_len;
    }

    if (start < 0) start = 0;
    if (end < 0) end = 0;
    if (start > buf_len) return PyLong_FromLong(-1);
    if (end > buf_len) end = buf_len;
    if (start >= end) return PyLong_FromLong(-1);

    Py_ssize_t res = buf->findcc(start, end, (uint32_t)class_mask, invert != 0);
    return PyLong_FromSsize_t(res);
}

/**
 * @brief rfindcc(self, class_mask, start=None, end=None, invert=False)
 * 
 * Find last character matching (or not matching) the specified character class(es).
 */
static PyObject* LStr_rfindcc(LStrObject *self, PyObject *args, PyObject *kwds) {
    static char *kwlist[] = {(char*)"class_mask", (char*)"start", (char*)"end", (char*)"invert", nullptr};
    unsigned long class_mask;
    PyObject *start_obj = Py_None;
    PyObject *end_obj = Py_None;
    int invert = 0;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "k|OOp:rfindcc", kwlist,
                                     &class_mask, &start_obj, &end_obj, &invert)) {
        return nullptr;
    }

    if (!self || !self->buffer) {
        PyErr_SetString(PyExc_RuntimeError, "invalid L object");
        return nullptr;
    }
    Buffer *buf = self->buffer;
    Py_ssize_t buf_len = (Py_ssize_t)buf->length();

    // Parse start/end similar to findc
    Py_ssize_t start;
    if (start_obj == Py_None) {
        start = 0;
    } else {
        if (!PyLong_Check(start_obj)) {
            PyErr_SetString(PyExc_TypeError, "start must be int or None");
            return nullptr;
        }
        start = PyLong_AsSsize_t(start_obj);
        if (start == -1 && PyErr_Occurred()) return nullptr;
        if (start < 0) start += buf_len;
    }

    Py_ssize_t end;
    if (end_obj == Py_None) {
        end = buf_len;
    } else {
        if (!PyLong_Check(end_obj)) {
            PyErr_SetString(PyExc_TypeError, "end must be int or None");
            return nullptr;
        }
        end = PyLong_AsSsize_t(end_obj);
        if (end == -1 && PyErr_Occurred()) return nullptr;
        if (end < 0) end += buf_len;
    }

    if (start < 0) start = 0;
    if (end < 0) end = 0;
    if (start > buf_len) return PyLong_FromLong(-1);
    if (end > buf_len) end = buf_len;
    if (start >= end) return PyLong_FromLong(-1);

    Py_ssize_t res = buf->rfindcc(start, end, (uint32_t)class_mask, invert != 0);
    return PyLong_FromSsize_t(res);
}

