/**
 * @file lstring_methods.cxx
 * @brief Method implementations and method table for `L`.
 */

#include <Python.h>
#include <cstring>
#include "lstring_utils.hxx"
#include "lstring/lstring.hxx"
#include "charset.hxx"
#include "str_buffer.hxx"
#include "tptr.hxx"

static PyTypeObject* get_base_l_type(PyTypeObject *type_self) {
    PyTypeObject *base_type = type_self;
    while (base_type->tp_base != nullptr &&
           strcmp(base_type->tp_name, "_lstring.L") != 0) {
        base_type = base_type->tp_base;
    }
    return base_type;
}

static int get_charset_source(LStrObject *self, PyObject *charset_obj, cppy::ptr &out_unicode, Buffer* &out_buffer) {
    out_unicode = cppy::ptr();
    out_buffer = nullptr;

    if (PyUnicode_Check(charset_obj)) {
        out_unicode = cppy::ptr(charset_obj, /*incref=*/true);
        return 0;
    }

    // Check if charset is an L instance (including subclasses)
    PyTypeObject *base_type = get_base_l_type(Py_TYPE(self));

    if (PyObject_IsInstance(charset_obj, (PyObject*)base_type) == 1) {
        LStrObject *charset_lstr = (LStrObject*)charset_obj;
        if (!charset_lstr->buffer) {
            PyErr_SetString(PyExc_RuntimeError, "charset L has no buffer");
            return -1;
        }

        // Fast-path: avoid materializing if charset is already a str buffer.
        if (charset_lstr->buffer->is_str()) {
            PyObject *u = ((StrBuffer*)charset_lstr->buffer)->get_str();
            out_unicode = cppy::ptr(u, /*incref=*/true);
            return 0;
        }

        out_buffer = charset_lstr->buffer;
        return 0;
    }

    PyErr_SetString(PyExc_TypeError, "charset must be str or L instance");
    return -1;
}
static PyObject* LStr_find(LStrObject *self, PyObject *args, PyObject *kwds);
static PyObject* LStr_rfind(LStrObject *self, PyObject *args, PyObject *kwds);
static PyObject* LStr_findc(LStrObject *self, PyObject *args, PyObject *kwds);
static PyObject* LStr_rfindc(LStrObject *self, PyObject *args, PyObject *kwds);
static PyObject* LStr_findcs(LStrObject *self, PyObject *args, PyObject *kwds);
static PyObject* LStr_rfindcs(LStrObject *self, PyObject *args, PyObject *kwds);
static PyObject* LStr_findcr(LStrObject *self, PyObject *args, PyObject *kwds);
static PyObject* LStr_rfindcr(LStrObject *self, PyObject *args, PyObject *kwds);
static PyObject* LStr_findcc(LStrObject *self, PyObject *args, PyObject *kwds);
static PyObject* LStr_rfindcc(LStrObject *self, PyObject *args, PyObject *kwds);
static PyObject* LStr_parse_printf_positional(LStrObject *self, PyObject *args, PyObject *kwds);
static PyObject* LStr_parse_printf_named(LStrObject *self, PyObject *args, PyObject *kwds);
static PyObject* LStr_parse_format_placeholder(LStrObject *self, PyObject *args, PyObject *kwds);
static PyObject* LStr_parse_fformat_placeholder(LStrObject *self, PyObject *args, PyObject *kwds);

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
    {"find", (PyCFunction)LStr_find, METH_VARARGS | METH_KEYWORDS, "Find substring like str.find(sub, start=None, end=None)"},
    {"rfind", (PyCFunction)LStr_rfind, METH_VARARGS | METH_KEYWORDS, "Find last occurrence like str.rfind(sub, start=None, end=None)"},
    {"findc", (PyCFunction)LStr_findc, METH_VARARGS | METH_KEYWORDS, "Find single code point: findc(ch, start=None, end=None)"},
    {"rfindc", (PyCFunction)LStr_rfindc, METH_VARARGS | METH_KEYWORDS, "Find single code point from right: rfindc(ch, start=None, end=None)"},
    {"findcs", (PyCFunction)LStr_findcs, METH_VARARGS | METH_KEYWORDS, "Find any character from set: findcs(charset, start=None, end=None, invert=False)"},
    {"rfindcs", (PyCFunction)LStr_rfindcs, METH_VARARGS | METH_KEYWORDS, "Find any character from set from right: rfindcs(charset, start=None, end=None, invert=False)"},
    {"findcr", (PyCFunction)LStr_findcr, METH_VARARGS | METH_KEYWORDS, "Find character in code point range: findcr(startcp, endcp, start=None, end=None, invert=False)"},
    {"rfindcr", (PyCFunction)LStr_rfindcr, METH_VARARGS | METH_KEYWORDS, "Find character in code point range from right: rfindcr(startcp, endcp, start=None, end=None, invert=False)"},
    {"findcc", (PyCFunction)LStr_findcc, METH_VARARGS | METH_KEYWORDS, "Find character by class: findcc(class_mask, start=None, end=None, invert=False)"},
    {"rfindcc", (PyCFunction)LStr_rfindcc, METH_VARARGS | METH_KEYWORDS, "Find character by class from right: rfindcc(class_mask, start=None, end=None, invert=False)"},
    {"_parse_printf_positional", (PyCFunction)LStr_parse_printf_positional, METH_VARARGS | METH_KEYWORDS, "Parse positional printf placeholder: _parse_printf_positional(start_pos) -> (end_pos, is_escape, star_count)"},
    {"_parse_printf_named", (PyCFunction)LStr_parse_printf_named, METH_VARARGS | METH_KEYWORDS, "Parse named printf placeholder: _parse_printf_named(start_pos) -> (end_pos, is_escape, name_end)"},
    {"_parse_format_placeholder", (PyCFunction)LStr_parse_format_placeholder, METH_VARARGS | METH_KEYWORDS, "Parse format placeholder: _parse_format_placeholder(start_pos) -> (end_pos, token_type, content_end)"},
    {"_parse_fformat_placeholder", (PyCFunction)LStr_parse_fformat_placeholder, METH_VARARGS | METH_KEYWORDS, "Parse f-string placeholder: _parse_fformat_placeholder(start_pos) -> (end_pos, token_type, content_end, expr_end)"},
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
    } else if (PyObject_IsInstance(sub_obj, (PyObject*)get_base_l_type(Py_TYPE(self))) == 1) {
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
    } else if (PyObject_IsInstance(sub_obj, (PyObject*)get_base_l_type(Py_TYPE(self))) == 1) {
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
 * @brief findcs(self, charset, start=None, end=None, invert=False)
 * 
 * Find first occurrence of any character from charset.
 * If invert=True, find first character NOT in charset.
 */
static PyObject* LStr_findcs(LStrObject *self, PyObject *args, PyObject *kwds) {
    static char *kwlist[] = {(char*)"charset", (char*)"start", (char*)"end", (char*)"invert", nullptr};
    PyObject *charset_obj = nullptr;
    PyObject *start_obj = Py_None;
    PyObject *end_obj = Py_None;
    int invert = 0;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O|OOp:findcs", kwlist,
                                     &charset_obj, &start_obj, &end_obj, &invert)) {
        return nullptr;
    }

    if (!self || !self->buffer) {
        PyErr_SetString(PyExc_RuntimeError, "invalid L object");
        return nullptr;
    }
    Buffer *buf = self->buffer;
    Py_ssize_t buf_len = (Py_ssize_t)buf->length();

    cppy::ptr charset_u;
    Buffer* charset_buf = nullptr;
    if (get_charset_source(self, charset_obj, charset_u, charset_buf) < 0) {
        return nullptr;
    }

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

    try {
        if (charset_buf) {
            const Py_ssize_t charset_len = charset_buf->length();
            if (charset_len <= 0) {
                FullCharSet empty;
                Py_ssize_t res = buf->findcs(start, end, empty, invert != 0);
                return PyLong_FromSsize_t(res);
            }

            FullCharSet cs(*charset_buf);
            Py_ssize_t res = buf->findcs(start, end, cs, invert != 0);
            return PyLong_FromSsize_t(res);
        }

        if (PyUnicode_READY(charset_u.get()) < 0) {
            return nullptr;
        }
        const Py_ssize_t charset_len = PyUnicode_GET_LENGTH(charset_u.get());
        if (charset_len <= 0) {
            FullCharSet empty;
            Py_ssize_t res = buf->findcs(start, end, empty, invert != 0);
            return PyLong_FromSsize_t(res);
        }

        const int kind = PyUnicode_KIND(charset_u.get());
        const void *data = PyUnicode_DATA(charset_u.get());
        Py_ssize_t res;
        if (kind == PyUnicode_1BYTE_KIND) {
            ByteCharSet cs((const Py_UCS1*)data, charset_len);
            res = buf->findcs(start, end, cs, invert != 0);
        } else if (kind == PyUnicode_2BYTE_KIND) {
            FullCharSet cs((const Py_UCS2*)data, charset_len);
            res = buf->findcs(start, end, cs, invert != 0);
        } else {
            FullCharSet cs((const Py_UCS4*)data, charset_len);
            res = buf->findcs(start, end, cs, invert != 0);
        }
        return PyLong_FromSsize_t(res);
    } catch (const std::exception& e) {
        PyErr_SetString(PyExc_RuntimeError, e.what());
        return nullptr;
    }
}


/**
 * @brief rfindcs(self, charset, start=None, end=None, invert=False)
 * 
 * Find last occurrence of any character from charset.
 * If invert=True, find last character NOT in charset.
 */
static PyObject* LStr_rfindcs(LStrObject *self, PyObject *args, PyObject *kwds) {
    static char *kwlist[] = {(char*)"charset", (char*)"start", (char*)"end", (char*)"invert", nullptr};
    PyObject *charset_obj = nullptr;
    PyObject *start_obj = Py_None;
    PyObject *end_obj = Py_None;
    int invert = 0;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O|OOp:rfindcs", kwlist,
                                     &charset_obj, &start_obj, &end_obj, &invert)) {
        return nullptr;
    }

    if (!self || !self->buffer) {
        PyErr_SetString(PyExc_RuntimeError, "invalid L object");
        return nullptr;
    }
    Buffer *buf = self->buffer;
    Py_ssize_t buf_len = (Py_ssize_t)buf->length();

    cppy::ptr charset_u;
    Buffer* charset_buf = nullptr;
    if (get_charset_source(self, charset_obj, charset_u, charset_buf) < 0) {
        return nullptr;
    }

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

    try {
        if (charset_buf) {
            const Py_ssize_t charset_len = charset_buf->length();
            if (charset_len <= 0) {
                FullCharSet empty;
                Py_ssize_t res = buf->rfindcs(start, end, empty, invert != 0);
                return PyLong_FromSsize_t(res);
            }

            FullCharSet cs(*charset_buf);
            Py_ssize_t res = buf->rfindcs(start, end, cs, invert != 0);
            return PyLong_FromSsize_t(res);
        }

        if (PyUnicode_READY(charset_u.get()) < 0) {
            return nullptr;
        }
        const Py_ssize_t charset_len = PyUnicode_GET_LENGTH(charset_u.get());
        if (charset_len <= 0) {
            FullCharSet empty;
            Py_ssize_t res = buf->rfindcs(start, end, empty, invert != 0);
            return PyLong_FromSsize_t(res);
        }

        const int kind = PyUnicode_KIND(charset_u.get());
        const void *data = PyUnicode_DATA(charset_u.get());
        Py_ssize_t res;
        if (kind == PyUnicode_1BYTE_KIND) {
            ByteCharSet cs((const Py_UCS1*)data, charset_len);
            res = buf->rfindcs(start, end, cs, invert != 0);
        } else if (kind == PyUnicode_2BYTE_KIND) {
            FullCharSet cs((const Py_UCS2*)data, charset_len);
            res = buf->rfindcs(start, end, cs, invert != 0);
        } else {
            FullCharSet cs((const Py_UCS4*)data, charset_len);
            res = buf->rfindcs(start, end, cs, invert != 0);
        }
        return PyLong_FromSsize_t(res);
    } catch (const std::exception& e) {
        PyErr_SetString(PyExc_RuntimeError, e.what());
        return nullptr;
    }
}


/**
 * @brief findcr(self, startcp, endcp, start=None, end=None, invert=False)
 * 
 * Find first occurrence of any character in code point range [startcp, endcp).
 * If invert=True, find first character NOT in the range.
 */
static PyObject* LStr_findcr(LStrObject *self, PyObject *args, PyObject *kwds) {
    static char *kwlist[] = {(char*)"startcp", (char*)"endcp", (char*)"start", (char*)"end", (char*)"invert", nullptr};
    PyObject *startcp_obj = nullptr;
    PyObject *endcp_obj = nullptr;
    PyObject *start_obj = Py_None;
    PyObject *end_obj = Py_None;
    int invert = 0;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "OO|OOp:findcr", kwlist,
                                     &startcp_obj, &endcp_obj, &start_obj, &end_obj, &invert)) {
        return nullptr;
    }

    if (!self || !self->buffer) {
        PyErr_SetString(PyExc_RuntimeError, "invalid L object");
        return nullptr;
    }
    Buffer *buf = self->buffer;
    Py_ssize_t buf_len = (Py_ssize_t)buf->length();

    // Parse startcp: accept int or 1-char str
    uint32_t startcp;
    if (PyLong_Check(startcp_obj)) {
        long tmp = PyLong_AsLong(startcp_obj);
        if (tmp == -1 && PyErr_Occurred()) return nullptr;
        if (tmp < 0) {
            PyErr_SetString(PyExc_ValueError, "startcp must be a non-negative code point");
            return nullptr;
        }
        startcp = (uint32_t)tmp;
    } else if (PyUnicode_Check(startcp_obj)) {
        if (PyUnicode_GetLength(startcp_obj) != 1) {
            PyErr_SetString(PyExc_ValueError, "startcp must be an int or single character string");
            return nullptr;
        }
        Py_UCS4 u = PyUnicode_ReadChar(startcp_obj, 0);
        startcp = (uint32_t)u;
    } else {
        PyErr_SetString(PyExc_TypeError, "startcp must be int or 1-char str");
        return nullptr;
    }

    // Parse endcp: accept int or 1-char str
    uint32_t endcp;
    if (PyLong_Check(endcp_obj)) {
        long tmp = PyLong_AsLong(endcp_obj);
        if (tmp == -1 && PyErr_Occurred()) return nullptr;
        if (tmp < 0) {
            PyErr_SetString(PyExc_ValueError, "endcp must be a non-negative code point");
            return nullptr;
        }
        endcp = (uint32_t)tmp;
    } else if (PyUnicode_Check(endcp_obj)) {
        if (PyUnicode_GetLength(endcp_obj) != 1) {
            PyErr_SetString(PyExc_ValueError, "endcp must be an int or single character string");
            return nullptr;
        }
        Py_UCS4 u = PyUnicode_ReadChar(endcp_obj, 0);
        endcp = (uint32_t)u;
    } else {
        PyErr_SetString(PyExc_TypeError, "endcp must be int or 1-char str");
        return nullptr;
    }

    if (startcp >= endcp) {
        PyErr_SetString(PyExc_ValueError, "startcp must be less than endcp");
        return nullptr;
    }

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

    Py_ssize_t res = buf->findcr(start, end, startcp, endcp, invert != 0);
    return PyLong_FromSsize_t(res);
}


/**
 * @brief rfindcr(self, startcp, endcp, start=None, end=None, invert=False)
 * 
 * Find last occurrence of any character in code point range [startcp, endcp).
 * If invert=True, find last character NOT in the range.
 */
static PyObject* LStr_rfindcr(LStrObject *self, PyObject *args, PyObject *kwds) {
    static char *kwlist[] = {(char*)"startcp", (char*)"endcp", (char*)"start", (char*)"end", (char*)"invert", nullptr};
    PyObject *startcp_obj = nullptr;
    PyObject *endcp_obj = nullptr;
    PyObject *start_obj = Py_None;
    PyObject *end_obj = Py_None;
    int invert = 0;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "OO|OOp:rfindcr", kwlist,
                                     &startcp_obj, &endcp_obj, &start_obj, &end_obj, &invert)) {
        return nullptr;
    }

    if (!self || !self->buffer) {
        PyErr_SetString(PyExc_RuntimeError, "invalid L object");
        return nullptr;
    }
    Buffer *buf = self->buffer;
    Py_ssize_t buf_len = (Py_ssize_t)buf->length();

    // Parse startcp: accept int or 1-char str
    uint32_t startcp;
    if (PyLong_Check(startcp_obj)) {
        long tmp = PyLong_AsLong(startcp_obj);
        if (tmp == -1 && PyErr_Occurred()) return nullptr;
        if (tmp < 0) {
            PyErr_SetString(PyExc_ValueError, "startcp must be a non-negative code point");
            return nullptr;
        }
        startcp = (uint32_t)tmp;
    } else if (PyUnicode_Check(startcp_obj)) {
        if (PyUnicode_GetLength(startcp_obj) != 1) {
            PyErr_SetString(PyExc_ValueError, "startcp must be an int or single character string");
            return nullptr;
        }
        Py_UCS4 u = PyUnicode_ReadChar(startcp_obj, 0);
        startcp = (uint32_t)u;
    } else {
        PyErr_SetString(PyExc_TypeError, "startcp must be int or 1-char str");
        return nullptr;
    }

    // Parse endcp: accept int or 1-char str
    uint32_t endcp;
    if (PyLong_Check(endcp_obj)) {
        long tmp = PyLong_AsLong(endcp_obj);
        if (tmp == -1 && PyErr_Occurred()) return nullptr;
        if (tmp < 0) {
            PyErr_SetString(PyExc_ValueError, "endcp must be a non-negative code point");
            return nullptr;
        }
        endcp = (uint32_t)tmp;
    } else if (PyUnicode_Check(endcp_obj)) {
        if (PyUnicode_GetLength(endcp_obj) != 1) {
            PyErr_SetString(PyExc_ValueError, "endcp must be an int or single character string");
            return nullptr;
        }
        Py_UCS4 u = PyUnicode_ReadChar(endcp_obj, 0);
        endcp = (uint32_t)u;
    } else {
        PyErr_SetString(PyExc_TypeError, "endcp must be int or 1-char str");
        return nullptr;
    }

    if (startcp >= endcp) {
        PyErr_SetString(PyExc_ValueError, "startcp must be less than endcp");
        return nullptr;
    }

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

    Py_ssize_t res = buf->rfindcr(start, end, startcp, endcp, invert != 0);
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


/**
 * @brief Check if character is a printf flag character (#, 0, space, +, -)
 */
static inline bool _is_printf_flag_char(uint32_t ch) {
    switch (ch) {
        case '#': case '0': case ' ': case '+': case '-':
            return true;
        default:
            return false;
    }
}

/**
 * @brief Check if character is a printf length modifier (h, l, L)
 */
static inline bool _is_printf_length_char(uint32_t ch) {
    switch (ch) {
        case 'h': case 'l': case 'L':
            return true;
        default:
            return false;
    }
}

/**
 * @brief Check if character is a printf type specifier
 */
static inline bool _is_printf_type_char(uint32_t ch) {
    switch (ch) {
        case 'd': case 'i': case 'o': case 'u':
        case 'x': case 'X': case 'e': case 'E':
        case 'f': case 'F': case 'g': case 'G':
        case 'c': case 'r': case 's': case 'a':
            return true;
        default:
            return false;
    }
}

/**
 * @brief parse_printf_positional(self, start_pos)
 *
 * Parse a positional printf-style placeholder starting at start_pos.
 * Returns a tuple: (end_pos, is_escape, star_count) where:
 *   - end_pos: Position after the placeholder (-1 if invalid)
 *   - is_escape: True if this is %% escape sequence
 *   - star_count: Number of * wildcards in width/precision
 */
static PyObject* LStr_parse_printf_positional(LStrObject *self, PyObject *args, PyObject *kwds) {
    static char *kwlist[] = {(char*)"start_pos", nullptr};
    Py_ssize_t start_pos;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "n:parse_printf_positional", kwlist, &start_pos)) {
        return nullptr;
    }

    if (!self || !self->buffer) {
        PyErr_SetString(PyExc_RuntimeError, "invalid L object");
        return nullptr;
    }
    Buffer *buf = self->buffer;
    Py_ssize_t length = (Py_ssize_t)buf->length();

    if (start_pos < 0 || start_pos >= length) {
        PyErr_SetString(PyExc_ValueError, "start_pos out of range");
        return nullptr;
    }

    // Must start with %
    if (buf->value(start_pos) != '%') {
        PyErr_SetString(PyExc_ValueError, "start_pos must point to %");
        return nullptr;
    }

    Py_ssize_t pos = start_pos + 1;
    
    if (pos >= length) {
        return Py_BuildValue("(nOi)", -1, Py_False, 0);
    }
    
    // Check for %% escape
    if (buf->value(pos) == '%') {
        return Py_BuildValue("(nOi)", pos + 1, Py_True, 0);
    }
    
    int star_count = 0;
    
    // Parse flags: #, 0, -, space, +
    while (pos < length && _is_printf_flag_char(buf->value(pos))) {
        pos++;
    }
    
    // Parse width: number or *
    if (pos < length && buf->value(pos) == '*') {
        star_count++;
        pos++;
    } else {
        while (pos < length && buf->value(pos) >= '0' && buf->value(pos) <= '9') {
            pos++;
        }
    }
    
    // Parse precision: .number or .*
    if (pos < length && buf->value(pos) == '.') {
        pos++;
        if (pos < length && buf->value(pos) == '*') {
            star_count++;
            pos++;
        } else {
            while (pos < length && buf->value(pos) >= '0' && buf->value(pos) <= '9') {
                pos++;
            }
        }
    }
    
    // Parse length: h, l, L
    if (pos < length && _is_printf_length_char(buf->value(pos))) {
        pos++;
    }
    
    // Parse type: d, i, o, u, x, X, e, E, f, F, g, G, c, r, s, a
    if (pos < length && _is_printf_type_char(buf->value(pos))) {
        return Py_BuildValue("(nOi)", pos + 1, Py_False, star_count);
    }
    
    // Invalid placeholder
    return Py_BuildValue("(nOi)", -1, Py_False, 0);
}


/**
 * @brief parse_printf_named(self, start_pos)
 *
 * Parse a named printf-style placeholder starting at start_pos.
 * Returns a tuple: (end_pos, is_escape, name_end) where:
 *   - end_pos: Position after the placeholder (-1 if invalid)
 *   - is_escape: True if this is %% escape sequence
 *   - name_end: Position after the closing ) of the name (-1 if not named)
 */
static PyObject* LStr_parse_printf_named(LStrObject *self, PyObject *args, PyObject *kwds) {
    static char *kwlist[] = {(char*)"start_pos", nullptr};
    Py_ssize_t start_pos;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "n:parse_printf_named", kwlist, &start_pos)) {
        return nullptr;
    }

    if (!self || !self->buffer) {
        PyErr_SetString(PyExc_RuntimeError, "invalid L object");
        return nullptr;
    }
    Buffer *buf = self->buffer;
    Py_ssize_t length = (Py_ssize_t)buf->length();

    if (start_pos < 0 || start_pos >= length) {
        PyErr_SetString(PyExc_ValueError, "start_pos out of range");
        return nullptr;
    }

    // Must start with %
    if (buf->value(start_pos) != '%') {
        PyErr_SetString(PyExc_ValueError, "start_pos must point to %");
        return nullptr;
    }

    Py_ssize_t pos = start_pos + 1;
    
    if (pos >= length) {
        return Py_BuildValue("(nOn)", -1, Py_False, -1);
    }
    
    // Check for %% escape
    if (buf->value(pos) == '%') {
        return Py_BuildValue("(nOn)", pos + 1, Py_True, -1);
    }
    
    // Check for named placeholder: %(name)
    Py_ssize_t name_end = -1;
    if (buf->value(pos) == '(') {
        pos++;
        // Find closing )
        while (pos < length && buf->value(pos) != ')') {
            pos++;
        }
        if (pos >= length) {
            return Py_BuildValue("(nOn)", -1, Py_False, -1);  // Unclosed (
        }
        pos++;  // Skip )
        name_end = pos;
    }
    
    // If not named, it's invalid for named placeholder parser
    if (name_end == -1) {
        return Py_BuildValue("(nOn)", -1, Py_False, -1);
    }
    
    // Parse flags: #, 0, -, space, +
    while (pos < length && _is_printf_flag_char(buf->value(pos))) {
        pos++;
    }
    
    // Parse width: number (no * for named)
    while (pos < length && buf->value(pos) >= '0' && buf->value(pos) <= '9') {
        pos++;
    }
    
    // Parse precision: .number (no * for named)
    if (pos < length && buf->value(pos) == '.') {
        pos++;
        while (pos < length && buf->value(pos) >= '0' && buf->value(pos) <= '9') {
            pos++;
        }
    }
    
    // Parse length: h, l, L
    if (pos < length && _is_printf_length_char(buf->value(pos))) {
        pos++;
    }
    
    // Parse type: d, i, o, u, x, X, e, E, f, F, g, G, c, r, s, a
    if (pos < length && _is_printf_type_char(buf->value(pos))) {
        return Py_BuildValue("(nOn)", pos + 1, Py_False, name_end);
    }
    
    // Invalid placeholder
    return Py_BuildValue("(nOn)", -1, Py_False, -1);
}


/**
 * @brief _parse_format_placeholder(self, start_pos)
 *
 * Parse a format() style placeholder or escape sequence starting at start_pos.
 * start_pos must point to { or } character.
 * 
 * Returns a tuple: (end_pos, token_type, content_end) where:
 *   - end_pos: Position after the token (-1 if invalid/unmatched)
 *   - token_type: 0=invalid, 1=literal_open ({{), 2=literal_close (}}), 3=placeholder
 *   - content_end: For placeholder - position before closing }, otherwise -1
 */
static PyObject* LStr_parse_format_placeholder(LStrObject *self, PyObject *args, PyObject *kwds) {
    static char *kwlist[] = {(char*)"start_pos", nullptr};
    Py_ssize_t start_pos;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "n:_parse_format_placeholder", kwlist, &start_pos)) {
        return nullptr;
    }

    if (!self || !self->buffer) {
        PyErr_SetString(PyExc_RuntimeError, "invalid L object");
        return nullptr;
    }
    Buffer *buf = self->buffer;
    Py_ssize_t length = (Py_ssize_t)buf->length();

    if (start_pos < 0 || start_pos >= length) {
        PyErr_SetString(PyExc_ValueError, "start_pos out of range");
        return nullptr;
    }

    uint32_t ch = buf->value(start_pos);
    
    if (ch == '{') {
        // Check for {{ escape
        if (start_pos + 1 < length && buf->value(start_pos + 1) == '{') {
            // Literal { escape sequence
            return Py_BuildValue("(nii)", start_pos + 2, 1, -1);
        }
        
        // Find matching } with nesting support
        Py_ssize_t pos = start_pos + 1;
        int depth = 1;
        
        while (pos < length && depth > 0) {
            uint32_t c = buf->value(pos);
            if (c == '{') {
                depth++;
            } else if (c == '}') {
                depth--;
            }
            pos++;
        }
        
        if (depth == 0) {
            // Found complete placeholder: {content}
            // content_end is position before closing }
            return Py_BuildValue("(nii)", pos, 3, pos - 1);
        } else {
            // Unclosed brace - invalid
            return Py_BuildValue("(nii)", -1, 0, -1);
        }
    } else if (ch == '}') {
        // Check for }} escape
        if (start_pos + 1 < length && buf->value(start_pos + 1) == '}') {
            // Literal } escape sequence
            return Py_BuildValue("(nii)", start_pos + 2, 2, -1);
        } else {
            // Unmatched } - invalid (caller should skip it)
            return Py_BuildValue("(nii)", start_pos + 1, 0, -1);
        }
    } else {
        PyErr_SetString(PyExc_ValueError, "start_pos must point to { or }");
        return nullptr;
    }
}


/**
 * @brief Find the end of a Python expression in an f-string placeholder.
 * 
 * Tracks nested brackets (), [], {} and quoted strings to find where the
 * expression ends (at : for format spec, ! for conversion, or } for end).
 * 
 * @param buf Buffer containing the format string
 * @param start Starting position (after opening {)
 * @param length Total buffer length
 * @return Position where expression ends, or -1 if not found
 */
static Py_ssize_t _find_fstring_expr_end(Buffer* buf, Py_ssize_t start, Py_ssize_t length) {
    int paren_depth = 0;
    int bracket_depth = 0;
    int brace_depth = 0;
    bool in_string = false;
    uint32_t quote_char = 0;
    bool is_raw = false;
    bool is_triple = false;
    
    for (Py_ssize_t i = start; i < length; i++) {
        uint32_t ch = buf->value(i);
        
        // Handle string literals
        if (!in_string) {
            // Check for raw string prefix
            if ((ch == 'r' || ch == 'R') && i + 1 < length) {
                uint32_t next = buf->value(i + 1);
                if (next == '\'' || next == '"') {
                    is_raw = true;
                    i++;
                    ch = buf->value(i);
                }
            }
            
            // Check for string start
            if (ch == '\'' || ch == '"') {
                in_string = true;
                quote_char = ch;
                // Check for triple-quoted string
                if (i + 2 < length && buf->value(i + 1) == ch && buf->value(i + 2) == ch) {
                    is_triple = true;
                    i += 2;
                }
                continue;
            }
        } else {
            // Inside string - look for end
            if (is_triple) {
                // Triple-quoted string ends with three quotes
                if (ch == quote_char && i + 2 < length && 
                    buf->value(i + 1) == quote_char && buf->value(i + 2) == quote_char) {
                    if (!is_raw || i == start || buf->value(i - 1) != '\\') {
                        in_string = false;
                        is_triple = false;
                        is_raw = false;
                        i += 2;
                        continue;
                    }
                }
            } else {
                // Single-quoted string
                if (ch == quote_char) {
                    if (!is_raw || i == start || buf->value(i - 1) != '\\') {
                        in_string = false;
                        is_raw = false;
                        continue;
                    }
                }
            }
            // Skip everything inside strings
            continue;
        }
        
        // Track bracket depth (only outside strings)
        if (ch == '(') {
            paren_depth++;
        } else if (ch == ')') {
            paren_depth--;
            if (paren_depth < 0) return -1;  // Unbalanced
        } else if (ch == '[') {
            bracket_depth++;
        } else if (ch == ']') {
            bracket_depth--;
            if (bracket_depth < 0) return -1;  // Unbalanced
        } else if (ch == '{') {
            brace_depth++;
        } else if (ch == '}') {
            // Closing brace at depth 0 ends the placeholder
            if (brace_depth == 0 && paren_depth == 0 && bracket_depth == 0) {
                return i;
            }
            brace_depth--;
            if (brace_depth < 0) return -1;  // Unbalanced
        } else if ((ch == ':' || ch == '!') && paren_depth == 0 && bracket_depth == 0 && brace_depth == 0) {
            // Format spec or conversion at depth 0
            return i;
        }
    }
    
    return -1;  // Unclosed expression
}


/**
 * @brief _parse_fformat_placeholder(self, start_pos)
 *
 * Parse an f-string style placeholder or escape sequence starting at start_pos.
 * start_pos must point to { or } character.
 * 
 * Returns a tuple: (end_pos, token_type, content_end, expr_end) where:
 *   - end_pos: Position after the token (-1 if invalid/unmatched)
 *   - token_type: 0=invalid, 1=literal {{ (open), 2=literal }} (close), 3=placeholder
 *   - content_end: For placeholder - position before closing }, otherwise -1
 *   - expr_end: For placeholder - position where expression ends (before : ! or }), otherwise -1
 */
static PyObject* LStr_parse_fformat_placeholder(LStrObject *self, PyObject *args, PyObject *kwds) {
    static char *kwlist[] = {(char*)"start_pos", nullptr};
    Py_ssize_t start_pos;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "n:_parse_fformat_placeholder", kwlist, &start_pos)) {
        return nullptr;
    }

    if (!self || !self->buffer) {
        PyErr_SetString(PyExc_RuntimeError, "invalid L object");
        return nullptr;
    }
    Buffer *buf = self->buffer;
    Py_ssize_t length = (Py_ssize_t)buf->length();

    if (start_pos < 0 || start_pos >= length) {
        PyErr_SetString(PyExc_ValueError, "start_pos out of range");
        return nullptr;
    }

    uint32_t ch = buf->value(start_pos);
    
    if (ch == '{') {
        // Check for {{ escape
        if (start_pos + 1 < length && buf->value(start_pos + 1) == '{') {
            // Literal { escape sequence
            return Py_BuildValue("(niii)", start_pos + 2, 1, -1, -1);
        }
        
        // Find end of expression
        Py_ssize_t expr_end = _find_fstring_expr_end(buf, start_pos + 1, length);
        
        if (expr_end == -1) {
            // Unclosed or invalid expression
            return Py_BuildValue("(niii)", -1, 0, -1, -1);
        }
        
        // Now find the actual closing }
        Py_ssize_t pos = expr_end;
        uint32_t end_ch = buf->value(pos);
        
        if (end_ch == '!') {
            // Conversion: !r, !s, !a
            pos++;
            if (pos < length) {
                uint32_t conv = buf->value(pos);
                if (conv == 'r' || conv == 's' || conv == 'a') {
                    pos++;
                } else {
                    // Invalid conversion
                    return Py_BuildValue("(niii)", -1, 0, -1, -1);
                }
            }
            // After conversion, might have format spec
            if (pos < length && buf->value(pos) == ':') {
                // Skip format spec (everything until })
                while (pos < length && buf->value(pos) != '}') {
                    pos++;
                }
            }
        } else if (end_ch == ':') {
            // Format spec - skip until }
            pos++;
            while (pos < length && buf->value(pos) != '}') {
                pos++;
            }
        }
        // end_ch == '}' - just close
        
        if (pos >= length || buf->value(pos) != '}') {
            // Missing closing brace
            return Py_BuildValue("(niii)", -1, 0, -1, -1);
        }
        
        // Found complete placeholder: {expr[!conv][:spec]}
        return Py_BuildValue("(niii)", pos + 1, 3, pos, expr_end);
        
    } else if (ch == '}') {
        // Check for }} escape
        if (start_pos + 1 < length && buf->value(start_pos + 1) == '}') {
            // Literal } escape sequence
            return Py_BuildValue("(niii)", start_pos + 2, 2, -1, -1);
        } else {
            // Unmatched } - invalid (caller should skip it)
            return Py_BuildValue("(niii)", start_pos + 1, 0, -1, -1);
        }
    } else {
        PyErr_SetString(PyExc_ValueError, "start_pos must point to { or }");
        return nullptr;
    }
}
