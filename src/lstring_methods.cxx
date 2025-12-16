/**
 * @file lstring_methods.cxx
 * @brief Method implementations and method table for `_lstr`.
 */

#include <Python.h>
#include "lstring.hxx"
#include "lstring_utils.hxx"
#include "buffer.hxx"
#include "str_buffer.hxx"

static PyObject* LStr_collapse(LStrObject *self, PyObject *Py_UNUSED(ignored));
static PyObject* LStr_find(LStrObject *self, PyObject *args, PyObject *kwds);
static PyObject* LStr_rfind(LStrObject *self, PyObject *args, PyObject *kwds);
static PyObject* LStr_findc(LStrObject *self, PyObject *args, PyObject *kwds);
static PyObject* LStr_rfindc(LStrObject *self, PyObject *args, PyObject *kwds);

/**
 * @brief Method table for the lstr type.
 *
 * Contains Python-callable methods exposed on the `_lstr` type. Each entry
 * maps a method name to a C function and calling convention.
 */
PyMethodDef LStr_methods[] = {
    {"collapse", (PyCFunction)LStr_collapse, METH_NOARGS, "Collapse internal buffer to a contiguous str buffer"},
    {"find", (PyCFunction)LStr_find, METH_VARARGS | METH_KEYWORDS, "Find substring like str.find(sub, start=None, end=None)"},
    {"rfind", (PyCFunction)LStr_rfind, METH_VARARGS | METH_KEYWORDS, "Find last occurrence like str.rfind(sub, start=None, end=None)"},
    {"findc", (PyCFunction)LStr_findc, METH_VARARGS | METH_KEYWORDS, "Find single code point: findc(ch, start=None, end=None)"},
    {"rfindc", (PyCFunction)LStr_rfindc, METH_VARARGS | METH_KEYWORDS, "Find single code point from right: rfindc(ch, start=None, end=None)"},
    {nullptr, nullptr, 0, nullptr}
};


/**
 * @brief Find method: search for a substring in the lstr.
 *
 * Signature: find(self, sub, start=None, end=None)
 * Accepts `sub` as either a Python str or another _lstr. Negative start/end
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
        PyErr_SetString(PyExc_RuntimeError, "invalid lstr object");
        return nullptr;
    }
    Buffer *src = self->buffer;
    Py_ssize_t src_len = (Py_ssize_t)src->length();

    // Obtain a Buffer for sub: accept Python str or _lstr
    Buffer *sub_buf = nullptr;
    cppy::ptr sub_owner;
    if (PyUnicode_Check(sub_obj)) {
        // wrap Python str into a temporary `_lstr` via factory and own it
        PyTypeObject *type = Py_TYPE(self);
        PyObject *tmp = make_lstr_from_pystr(type, sub_obj);
        if (!tmp) return nullptr;
        sub_owner = cppy::ptr(tmp);
        sub_buf = ((LStrObject*)tmp)->buffer;
    } else if (PyObject_HasAttrString((PyObject*)Py_TYPE(sub_obj), "collapse")) {
        // assume it's an _lstr-like object
        LStrObject *lsub = (LStrObject*)sub_obj;
        if (!lsub->buffer) {
            PyErr_SetString(PyExc_RuntimeError, "substring lstr has no buffer");
            return nullptr;
        }
        sub_owner = cppy::ptr(sub_obj, true); // incref
        sub_buf = lsub->buffer;
    } else {
        PyErr_SetString(PyExc_TypeError, "sub must be str or _lstr");
        return nullptr;
    }

    Py_ssize_t sub_len = (Py_ssize_t)sub_buf->length();

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
    if (src->is_str() && sub_buf->is_str()) {
        PyObject *src_py = ((StrBuffer*)src)->get_str();
        PyObject *sub_py = ((StrBuffer*)sub_buf)->get_str();
        Py_ssize_t idx = PyUnicode_Find(src_py, sub_py, start, end, 1); // direction=1 -> find
        if (idx == -1 && PyErr_Occurred()) return nullptr;
        return PyLong_FromSsize_t(idx);
    }

    // Element-wise scanning using buffer->value()
    Py_ssize_t last = end - sub_len;
    for (Py_ssize_t i = start; i <= last; ++i) {
        bool match = true;
        for (Py_ssize_t j = 0; j < sub_len; ++j) {
            uint32_t a = src->value(i + j);
            uint32_t b = sub_buf->value(j);
            if (a != b) { match = false; break; }
        }
        if (match) return PyLong_FromSsize_t(i);
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
        PyErr_SetString(PyExc_RuntimeError, "invalid lstr object");
        return nullptr;
    }
    Buffer *src = self->buffer;
    Py_ssize_t src_len = (Py_ssize_t)src->length();

    // Obtain sub buffer (str or _lstr)
    Buffer *sub_buf = nullptr;
    cppy::ptr sub_owner;
    if (PyUnicode_Check(sub_obj)) {
        PyTypeObject *type = Py_TYPE(self);
        PyObject *tmp = make_lstr_from_pystr(type, sub_obj);
        if (!tmp) return nullptr;
        sub_owner = cppy::ptr(tmp);
        sub_buf = ((LStrObject*)tmp)->buffer;
    } else if (PyObject_HasAttrString((PyObject*)Py_TYPE(sub_obj), "collapse")) {
        LStrObject *lsub = (LStrObject*)sub_obj;
        if (!lsub->buffer) {
            PyErr_SetString(PyExc_RuntimeError, "substring lstr has no buffer");
            return nullptr;
        }
        sub_owner = cppy::ptr(sub_obj, true);
        sub_buf = lsub->buffer;
    } else {
        PyErr_SetString(PyExc_TypeError, "sub must be str or _lstr");
        return nullptr;
    }

    Py_ssize_t sub_len = (Py_ssize_t)sub_buf->length();

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
    if (src->is_str() && sub_buf->is_str()) {
        PyObject *src_py = ((StrBuffer*)src)->get_str();
        PyObject *sub_py = ((StrBuffer*)sub_buf)->get_str();
        Py_ssize_t idx = PyUnicode_Find(src_py, sub_py, start, end, -1); // direction=-1 -> rfind
        if (idx == -1 && PyErr_Occurred()) return nullptr;
        return PyLong_FromSsize_t(idx);
    }

    // Scan from the right: i goes from last down to start
    Py_ssize_t last = end - sub_len;
    for (Py_ssize_t i = last; i >= start; --i) {
        bool match = true;
        for (Py_ssize_t j = 0; j < sub_len; ++j) {
            uint32_t a = src->value(i + j);
            uint32_t b = sub_buf->value(j);
            if (a != b) { match = false; break; }
        }
        if (match) return PyLong_FromSsize_t(i);
        if (i == 0) break; // prevent underflow for Py_ssize_t
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
        PyErr_SetString(PyExc_RuntimeError, "invalid lstr object");
        return nullptr;
    }
    lstr_collapse(self);
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
        PyErr_SetString(PyExc_RuntimeError, "invalid lstr object");
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
        PyErr_SetString(PyExc_RuntimeError, "invalid lstr object");
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
