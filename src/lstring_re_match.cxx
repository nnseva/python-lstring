#include <Python.h>
#include "lstring_re_match.hxx"
#include "lstring_re_regex.hxx"
#include "slice_buffer.hxx"
#include "lstring_utils.hxx"
#include "tptr.hxx"
#include <cppy/cppy.h>

// Use the same CharT choice as other regex components in this build.
using CharT = Py_UCS4;

// Match.__new__(cls, pattern: Pattern, subject: L)
static PyObject*
Match_new(PyTypeObject *type, PyObject *args, PyObject *kwds) {
    // Allocate Match object without initialization
    MatchObject *self = (MatchObject*)type->tp_alloc(type, 0);
    if (!self) return nullptr;
    
    self->matchbuf = nullptr;
    
    return (PyObject*)self;
}

// Match.__init__(self, pattern: Pattern, subject: L)
static int
Match_init(PyObject *self_obj, PyObject *args, PyObject *kwds) {
    MatchObject *self = (MatchObject*)self_obj;
    PyObject *pattern_obj = nullptr;
    PyObject *subject_obj = nullptr;
    PyObject *pos_obj = nullptr;
    PyObject *endpos_obj = nullptr;
    Py_ssize_t pos = 0;
    Py_ssize_t endpos = 0;
    static char *kwlist[] = {(char*)"pattern", (char*)"subject", (char*)"pos", (char*)"endpos", nullptr};
    
    if (!PyArg_ParseTupleAndKeywords(args, kwds, "OO|OO", kwlist, &pattern_obj, &subject_obj, &pos_obj, &endpos_obj)) {
        return -1;
    }
    
    // Verify pattern is a Pattern instance
    cppy::ptr lmod(PyImport_ImportModule("_lstring"));
    if (!lmod) return -1;
    cppy::ptr re_sub(PyObject_GetAttrString(lmod.get(), "re"));
    if (!re_sub) return -1;
    cppy::ptr pattern_type(PyObject_GetAttrString(re_sub.get(), "Pattern"));
    if (!pattern_type) return -1;
    
    int is_pattern = PyObject_IsInstance(pattern_obj, pattern_type.get());
    if (is_pattern == -1) return -1;
    if (is_pattern == 0) {
        PyErr_SetString(PyExc_TypeError, "pattern must be an instance of _lstring.re.Pattern");
        return -1;
    }
    
    // Verify subject is lstring.L (no str conversion here)
    tptr<PyTypeObject> LType(get_string_lstr_type());
    if (!LType) return -1;
    int is_lstr = PyObject_IsInstance(subject_obj, LType.ptr().get());
    if (is_lstr == -1) return -1;
    if (is_lstr == 0) {
        PyErr_SetString(PyExc_TypeError, "subject must be lstring.L");
        return -1;
    }

    Py_ssize_t subject_len = reinterpret_cast<LStrObject*>(subject_obj)->buffer->length();

    // Parse pos/endpos. CPython clamps negatives to 0.
    pos = 0;
    if (pos_obj && pos_obj != Py_None) {
        pos = PyLong_AsSsize_t(pos_obj);
        if (pos == -1 && PyErr_Occurred()) return -1;
        if (pos < 0) pos = 0;
    }

    endpos = subject_len;
    if (endpos_obj && endpos_obj != Py_None) {
        endpos = PyLong_AsSsize_t(endpos_obj);
        if (endpos == -1 && PyErr_Occurred()) return -1;
        if (endpos < 0) endpos = 0;
    }

    if (pos > subject_len) pos = subject_len;
    if (endpos > subject_len) endpos = subject_len;
    if (endpos < pos) endpos = pos;
    
    // Create LStrMatchBuffer
    try {
        self->matchbuf = new LStrMatchBuffer<CharT>(pattern_obj, subject_obj, pos, endpos);
    } catch (const std::exception &e) {
        PyErr_SetString(PyExc_RuntimeError, e.what());
        return -1;
    }
    
    return 0;
}

static void
Match_dealloc(PyObject *self_obj) {
    MatchObject *self = (MatchObject*)self_obj;
    if (self->matchbuf) {
        auto *buf = reinterpret_cast<LStrMatchBuffer<CharT>*>(self->matchbuf);
        delete buf;
        self->matchbuf = nullptr;
    }
    Py_TYPE(self)->tp_free(self_obj);
}

// Match.string (read-only) -> subject object saved in match buffer
static PyObject*
Match_get_string(PyObject *self_obj, void * /*closure*/) {
    MatchObject *self = (MatchObject*)self_obj;
    if (!self->matchbuf) {
        PyErr_SetString(PyExc_AttributeError, "Match object not initialized");
        return nullptr;
    }
    return cppy::incref(reinterpret_cast<LStrMatchBuffer<CharT>*>(self->matchbuf)->where.ptr().get());
}

// Match.re (read-only) -> Pattern object saved in match buffer
static PyObject*
Match_get_re(PyObject *self_obj, void * /*closure*/) {
    MatchObject *self = (MatchObject*)self_obj;
    if (!self->matchbuf) {
        PyErr_SetString(PyExc_AttributeError, "Match object not initialized");
        return nullptr;
    }
    return cppy::incref(reinterpret_cast<LStrMatchBuffer<CharT>*>(self->matchbuf)->pattern.ptr().get());
}

// Match.pos (read-only) -> start position used for this match
static PyObject*
Match_get_pos(PyObject *self_obj, void * /*closure*/) {
    MatchObject *self = (MatchObject*)self_obj;
    if (!self->matchbuf) {
        PyErr_SetString(PyExc_AttributeError, "Match object not initialized");
        return nullptr;
    }
    return PyLong_FromSsize_t(reinterpret_cast<LStrMatchBuffer<CharT>*>(self->matchbuf)->pos);
}

// Match.endpos (read-only) -> end position used for this match
static PyObject*
Match_get_endpos(PyObject *self_obj, void * /*closure*/) {
    MatchObject *self = (MatchObject*)self_obj;
    if (!self->matchbuf) {
        PyErr_SetString(PyExc_AttributeError, "Match object not initialized");
        return nullptr;
    }
    return PyLong_FromSsize_t(reinterpret_cast<LStrMatchBuffer<CharT>*>(self->matchbuf)->endpos);
}

static PyGetSetDef Match_getset[] = {
    {(char*)"string", (getter)Match_get_string, nullptr, (char*)"Subject object used for this match (read-only).", nullptr},
    {(char*)"re", (getter)Match_get_re, nullptr, (char*)"Pattern object used for this match (read-only).", nullptr},
    {(char*)"pos", (getter)Match_get_pos, nullptr, (char*)"Start position passed to the pattern method (read-only).", nullptr},
    {(char*)"endpos", (getter)Match_get_endpos, nullptr, (char*)"End position passed to the pattern method (read-only).", nullptr},
    {nullptr, nullptr, nullptr, nullptr, nullptr}
};

// Helper: extract single group by index or name and return as L object
// Accepts only int (index) or lstring.L (name), no str conversion
static PyObject*
extract_group_by_index_or_name(LStrMatchBuffer<CharT> *buf, PyObject *arg_obj) {
    LStrIteratorBuffer<CharT> begin_iter(buf->where.get(), 0);

    // Use the concrete Python type of the subject (usually lstring.L) so that
    // extracted groups are created as that type rather than the base _lstring.L.
    PyTypeObject *subject_lstr_type = Py_TYPE(buf->where.ptr().get());
    tptr<PyTypeObject> lstr_type(subject_lstr_type, true);
    if (!lstr_type) return nullptr;
    
    // Check if argument is an integer (group index)
    if (PyLong_Check(arg_obj)) {
        Py_ssize_t group_index = PyLong_AsSsize_t(arg_obj);
        if (group_index == -1 && PyErr_Occurred()) return nullptr;
        
        Py_ssize_t num_groups = static_cast<Py_ssize_t>(buf->results.size());
        if (group_index < 0 || group_index >= num_groups) {
            PyErr_SetString(PyExc_IndexError, "no such group");
            return nullptr;
        }
        
        if (!buf->results[group_index].matched) {
            Py_RETURN_NONE;
        }
        
        Py_ssize_t start = begin_iter.distance_to(buf->results[group_index].first);
        Py_ssize_t end = begin_iter.distance_to(buf->results[group_index].second);
        
        tptr<LStrObject> result(PyType_GenericAlloc(lstr_type.get(), 0));
        if (!result) return nullptr;
        result->buffer = new Slice1Buffer(buf->where.ptr().get(), start, end);
        return result.ptr().release();
    }
    
    // Check if argument is lstring.L (group name)
    int is_lstr = PyObject_IsInstance(arg_obj, lstr_type.ptr().get());
    if (is_lstr == -1) return nullptr;
    if (is_lstr == 0) {
        PyErr_SetString(PyExc_TypeError, "group argument must be an integer or lstring.L");
        return nullptr;
    }
    
    LStrObject *name_lobj = reinterpret_cast<LStrObject*>(arg_obj);
    
    // Convert L to std::basic_string<CharT> for Boost
    LStrIteratorBuffer<CharT> name_begin(name_lobj, 0);
    LStrIteratorBuffer<CharT> name_end(name_lobj, name_begin.length());
    std::basic_string<CharT> group_name(name_begin, name_end);
    
    // Access named group via Boost's operator[]
    auto &sub = buf->results[group_name];
    if (!sub.matched) {
        Py_RETURN_NONE;
    }
    
    Py_ssize_t start = begin_iter.distance_to(sub.first);
    Py_ssize_t end = begin_iter.distance_to(sub.second);
    
    tptr<LStrObject> result(PyType_GenericAlloc(lstr_type.get(), 0));
    if (!result) return nullptr;
    result->buffer = new Slice1Buffer(buf->where.ptr().get(), start, end);
    return result.ptr().release();
}

// group(*indices) - return one or more subgroups of the match by index or name
static PyObject*
Match_group(PyObject *self_obj, PyObject *args) {
    MatchObject *self = (MatchObject*)self_obj;
    if (!self->matchbuf) {
        PyErr_SetString(PyExc_RuntimeError, "invalid Match object");
        return nullptr;
    }

    auto *buf = reinterpret_cast<LStrMatchBuffer<CharT>*>(self->matchbuf);
    Py_ssize_t num_groups = static_cast<Py_ssize_t>(buf->results.size());

    // If no arguments, default to group(0)
    Py_ssize_t nargs = PyTuple_GET_SIZE(args);
    if (nargs == 0) {
        // Return group 0 (full match)
        if (num_groups == 0 || !buf->results[0].matched) {
            Py_RETURN_NONE;
        }
        
        LStrIteratorBuffer<CharT> begin_iter(buf->where.get(), 0);
        Py_ssize_t start = begin_iter.distance_to(buf->results[0].first);
        Py_ssize_t end = begin_iter.distance_to(buf->results[0].second);
        
        PyTypeObject *subject_lstr_type = Py_TYPE(buf->where.ptr().get());
        tptr<PyTypeObject> lstr_type(subject_lstr_type, true);
        if (!lstr_type) return nullptr;
        tptr<LStrObject> result(PyType_GenericAlloc(lstr_type.get(), 0));
        if (!result) return nullptr;
        result->buffer = new Slice1Buffer(buf->where.ptr().get(), start, end);
        return result.ptr().release();
    }

    // If single argument, return single group
    if (nargs == 1) {
        return extract_group_by_index_or_name(buf, PyTuple_GET_ITEM(args, 0));
    }

    // Multiple arguments: return tuple of groups
    cppy::ptr result_tuple(PyTuple_New(nargs));
    if (!result_tuple) return nullptr;
    
    for (Py_ssize_t i = 0; i < nargs; ++i) {
        PyObject *group_value = extract_group_by_index_or_name(buf, PyTuple_GET_ITEM(args, i));
        if (!group_value) return nullptr;
        PyTuple_SET_ITEM(result_tuple.get(), i, group_value);
    }
    
    return result_tuple.release();
}

// groups(default=None) - return tuple of all capturing groups (excluding group 0)
static PyObject*
Match_groups(PyObject *self_obj, PyObject *args) {
    MatchObject *self = (MatchObject*)self_obj;
    if (!self->matchbuf) {
        PyErr_SetString(PyExc_RuntimeError, "invalid Match object");
        return nullptr;
    }

    PyObject *default_value = Py_None;
    if (!PyArg_ParseTuple(args, "|O", &default_value)) return nullptr;

    auto *buf = reinterpret_cast<LStrMatchBuffer<CharT>*>(self->matchbuf);
    Py_ssize_t num_groups = static_cast<Py_ssize_t>(buf->results.size());
    
    // groups() returns all groups except group 0 (full match)
    Py_ssize_t num_capturing_groups = num_groups > 0 ? num_groups - 1 : 0;
    
    cppy::ptr result_tuple(PyTuple_New(num_capturing_groups));
    if (!result_tuple) return nullptr;
    
    LStrIteratorBuffer<CharT> begin_iter(buf->where.get(), 0);

    PyTypeObject *subject_lstr_type = Py_TYPE(buf->where.ptr().get());
    tptr<PyTypeObject> lstr_type(subject_lstr_type, true);
    if (!lstr_type) return nullptr;
    
    for (Py_ssize_t i = 0; i < num_capturing_groups; ++i) {
        Py_ssize_t group_index = i + 1;  // Skip group 0
        PyObject *group_value;
        
        if (!buf->results[group_index].matched) {
            group_value = cppy::incref(default_value);
        } else {
            Py_ssize_t start = begin_iter.distance_to(buf->results[group_index].first);
            Py_ssize_t end = begin_iter.distance_to(buf->results[group_index].second);
            
            tptr<LStrObject> lobj(PyType_GenericAlloc(lstr_type.get(), 0));
            if (!lobj) return nullptr;
            lobj->buffer = new Slice1Buffer(buf->where.ptr().get(), start, end);
            group_value = lobj.ptr().release();
        }
        
        PyTuple_SET_ITEM(result_tuple.get(), i, group_value);
    }
    
    return result_tuple.release();
}

// __getitem__(index_or_name) - equivalent to group(index_or_name)
static PyObject*
Match_getitem(PyObject *self_obj, PyObject *key) {
    MatchObject *self = (MatchObject*)self_obj;
    if (!self->matchbuf) {
        PyErr_SetString(PyExc_RuntimeError, "invalid Match object");
        return nullptr;
    }

    auto *buf = reinterpret_cast<LStrMatchBuffer<CharT>*>(self->matchbuf);
    return extract_group_by_index_or_name(buf, key);
}

// Match.start(group=0) -> int
static PyObject* Match_start(PyObject *self_obj, PyObject *args) {
    MatchObject *self = (MatchObject*)self_obj;
    if (!self->matchbuf) {
        PyErr_SetString(PyExc_RuntimeError, "Match object not initialized");
        return nullptr;
    }

    auto *buf = reinterpret_cast<LStrMatchBuffer<CharT>*>(self->matchbuf);
    cppy::ptr group_arg;
    {
        PyObject *temp = nullptr;
        if (!PyArg_ParseTuple(args, "|O", &temp)) return nullptr;
        group_arg = temp ? cppy::ptr(temp, true) : cppy::ptr(PyLong_FromLong(0));
    }
    if (!group_arg) return nullptr;
    
    try {
        LStrIteratorBuffer<CharT> begin_iter(buf->where.get(), 0);
        
        // Handle integer index
        if (PyLong_Check(group_arg.get())) {
            int group_index = PyLong_AsLong(group_arg.get());
            if (group_index == -1 && PyErr_Occurred()) return nullptr;
            
            if (group_index < 0 || group_index >= static_cast<int>(buf->results.size())) {
                PyErr_SetString(PyExc_IndexError, "no such group");
                return nullptr;
            }
            
            if (!buf->results[group_index].matched) {
                return PyLong_FromLong(-1);
            }
            
            Py_ssize_t start_pos = begin_iter.distance_to(buf->results[group_index].first);
            return PyLong_FromSsize_t(start_pos);
        }
        
        // Handle L name
        tptr<PyTypeObject> lstr_type(get_string_lstr_type());
        if (!lstr_type) return nullptr;
        
        int is_lstr = PyObject_IsInstance(group_arg.get(), lstr_type.ptr().get());
        if (is_lstr == -1) return nullptr;
        if (is_lstr == 0) {
            PyErr_SetString(PyExc_TypeError, "group index or name must be int or lstring.L");
            return nullptr;
        }
        
        LStrObject *name_lobj = reinterpret_cast<LStrObject*>(group_arg.get());
        LStrIteratorBuffer<CharT> name_begin(name_lobj, 0);
        LStrIteratorBuffer<CharT> name_end(name_lobj, name_begin.length());
        std::basic_string<CharT> group_name(name_begin, name_end);
        
        auto &sub = buf->results[group_name];
        if (!sub.matched) {
            return PyLong_FromLong(-1);
        }
        
        Py_ssize_t start_pos = begin_iter.distance_to(sub.first);
        return PyLong_FromSsize_t(start_pos);
    } catch (const std::exception &e) {
        PyErr_SetString(PyExc_RuntimeError, e.what());
        return nullptr;
    }
}

// Match.end(group=0) -> int
static PyObject* Match_end(PyObject *self_obj, PyObject *args) {
    MatchObject *self = (MatchObject*)self_obj;
    if (!self->matchbuf) {
        PyErr_SetString(PyExc_RuntimeError, "Match object not initialized");
        return nullptr;
    }

    auto *buf = reinterpret_cast<LStrMatchBuffer<CharT>*>(self->matchbuf);
    cppy::ptr group_arg;
    {
        PyObject *temp = nullptr;
        if (!PyArg_ParseTuple(args, "|O", &temp)) return nullptr;
        group_arg = temp ? cppy::ptr(temp, true) : cppy::ptr(PyLong_FromLong(0));
    }
    if (!group_arg) return nullptr;
    
    try {
        LStrIteratorBuffer<CharT> begin_iter(buf->where.get(), 0);
        
        // Handle integer index
        if (PyLong_Check(group_arg.get())) {
            int group_index = PyLong_AsLong(group_arg.get());
            if (group_index == -1 && PyErr_Occurred()) return nullptr;
            
            if (group_index < 0 || group_index >= static_cast<int>(buf->results.size())) {
                PyErr_SetString(PyExc_IndexError, "no such group");
                return nullptr;
            }
            
            if (!buf->results[group_index].matched) {
                return PyLong_FromLong(-1);
            }
            
            Py_ssize_t end_pos = begin_iter.distance_to(buf->results[group_index].second);
            return PyLong_FromSsize_t(end_pos);
        }
        
        // Handle L name
        tptr<PyTypeObject> lstr_type(get_string_lstr_type());
        if (!lstr_type) return nullptr;
        
        int is_lstr = PyObject_IsInstance(group_arg.get(), lstr_type.ptr().get());
        if (is_lstr == -1) return nullptr;
        if (is_lstr == 0) {
            PyErr_SetString(PyExc_TypeError, "group index or name must be int or lstring.L");
            return nullptr;
        }
        
        LStrObject *name_lobj = reinterpret_cast<LStrObject*>(group_arg.get());
        LStrIteratorBuffer<CharT> name_begin(name_lobj, 0);
        LStrIteratorBuffer<CharT> name_end(name_lobj, name_begin.length());
        std::basic_string<CharT> group_name(name_begin, name_end);
        
        auto &sub = buf->results[group_name];
        if (!sub.matched) {
            return PyLong_FromLong(-1);
        }
        
        Py_ssize_t end_pos = begin_iter.distance_to(sub.second);
        return PyLong_FromSsize_t(end_pos);
    } catch (const std::exception &e) {
        PyErr_SetString(PyExc_RuntimeError, e.what());
        return nullptr;
    }
}

// Match.span(group=0) -> tuple[int, int]
static PyObject* Match_span(PyObject *self_obj, PyObject *args) {
    MatchObject *self = (MatchObject*)self_obj;
    if (!self->matchbuf) {
        PyErr_SetString(PyExc_RuntimeError, "Match object not initialized");
        return nullptr;
    }

    auto *buf = reinterpret_cast<LStrMatchBuffer<CharT>*>(self->matchbuf);
    cppy::ptr group_arg;
    {
        PyObject *temp = nullptr;
        if (!PyArg_ParseTuple(args, "|O", &temp)) return nullptr;
        group_arg = temp ? cppy::ptr(temp, true) : cppy::ptr(PyLong_FromLong(0));
    }
    if (!group_arg) return nullptr;
    
    try {
        LStrIteratorBuffer<CharT> begin_iter(buf->where.get(), 0);
        
        // Handle integer index
        if (PyLong_Check(group_arg.get())) {
            int group_index = PyLong_AsLong(group_arg.get());
            if (group_index == -1 && PyErr_Occurred()) return nullptr;
            
            if (group_index < 0 || group_index >= static_cast<int>(buf->results.size())) {
                PyErr_SetString(PyExc_IndexError, "no such group");
                return nullptr;
            }
            
            if (!buf->results[group_index].matched) {
                cppy::ptr result(PyTuple_New(2));
                if (!result) return nullptr;
                PyTuple_SET_ITEM(result.get(), 0, PyLong_FromLong(-1));
                PyTuple_SET_ITEM(result.get(), 1, PyLong_FromLong(-1));
                return result.release();
            }
            
            Py_ssize_t start_pos = begin_iter.distance_to(buf->results[group_index].first);
            Py_ssize_t end_pos = begin_iter.distance_to(buf->results[group_index].second);
            
            cppy::ptr result(PyTuple_New(2));
            if (!result) return nullptr;
            PyTuple_SET_ITEM(result.get(), 0, PyLong_FromSsize_t(start_pos));
            PyTuple_SET_ITEM(result.get(), 1, PyLong_FromSsize_t(end_pos));
            return result.release();
        }
        
        // Handle L name
        tptr<PyTypeObject> lstr_type(get_string_lstr_type());
        if (!lstr_type) return nullptr;
        
        int is_lstr = PyObject_IsInstance(group_arg.get(), lstr_type.ptr().get());
        if (is_lstr == -1) return nullptr;
        if (is_lstr == 0) {
            PyErr_SetString(PyExc_TypeError, "group index or name must be int or lstring.L");
            return nullptr;
        }
        
        LStrObject *name_lobj = reinterpret_cast<LStrObject*>(group_arg.get());
        LStrIteratorBuffer<CharT> name_begin(name_lobj, 0);
        LStrIteratorBuffer<CharT> name_end(name_lobj, name_begin.length());
        std::basic_string<CharT> group_name(name_begin, name_end);
        
        auto &sub = buf->results[group_name];
        if (!sub.matched) {
            cppy::ptr result(PyTuple_New(2));
            if (!result) return nullptr;
            PyTuple_SET_ITEM(result.get(), 0, PyLong_FromLong(-1));
            PyTuple_SET_ITEM(result.get(), 1, PyLong_FromLong(-1));
            return result.release();
        }
        
        Py_ssize_t start_pos = begin_iter.distance_to(sub.first);
        Py_ssize_t end_pos = begin_iter.distance_to(sub.second);
        
        cppy::ptr result(PyTuple_New(2));
        if (!result) return nullptr;
        PyTuple_SET_ITEM(result.get(), 0, PyLong_FromSsize_t(start_pos));
        PyTuple_SET_ITEM(result.get(), 1, PyLong_FromSsize_t(end_pos));
        return result.release();
    } catch (const std::exception &e) {
        PyErr_SetString(PyExc_RuntimeError, e.what());
        return nullptr;
    }
}

// Match.__repr__() -> str
static PyObject* Match_repr(PyObject *self_obj) {
    MatchObject *self = (MatchObject*)self_obj;
    if (!self->matchbuf) {
        return PyUnicode_FromString("<_lstring.re.Match object; not initialized>");
    }

    auto *buf = reinterpret_cast<LStrMatchBuffer<CharT>*>(self->matchbuf);
    
    try {
        // Get span (start, end) of the full match (group 0)
        if (buf->results.empty() || !buf->results[0].matched) {
            return PyUnicode_FromString("<_lstring.re.Match object; no match>");
        }

        LStrIteratorBuffer<CharT> begin_iter(buf->where.get(), 0);
        Py_ssize_t start_pos = begin_iter.distance_to(buf->results[0].first);
        Py_ssize_t end_pos = begin_iter.distance_to(buf->results[0].second);
        
        // Get the matched string
        PyTypeObject *subject_lstr_type = Py_TYPE(buf->where.ptr().get());
        tptr<PyTypeObject> lstr_type(subject_lstr_type, true);
        if (!lstr_type) return nullptr;
        
        tptr<LStrObject> match_lobj(PyType_GenericAlloc(lstr_type.get(), 0));
        if (!match_lobj) return nullptr;
        match_lobj->buffer = new Slice1Buffer(buf->where.ptr().get(), start_pos, end_pos);
        
        // Convert to Python str for display
        cppy::ptr match_str(PyObject_Str(match_lobj.ptr().get()));
        if (!match_str) return nullptr;
        
        // Format: <re.Match object; span=(start, end), match='...'>
        return PyUnicode_FromFormat("<_lstring.re.Match object; span=(%zd, %zd), match=%R>",
                                    start_pos, end_pos, match_str.get());
    } catch (const std::exception &e) {
        PyErr_SetString(PyExc_RuntimeError, e.what());
        return nullptr;
    }
}

static PyMethodDef Match_methods[] = {
    {"group", (PyCFunction)Match_group, METH_VARARGS, "Return subgroup by index or name."},
    {"groups", (PyCFunction)Match_groups, METH_VARARGS, "Return all groups as a tuple."},
    {"start", (PyCFunction)Match_start, METH_VARARGS, "Return start position of group."},
    {"end", (PyCFunction)Match_end, METH_VARARGS, "Return end position of group."},
    {"span", (PyCFunction)Match_span, METH_VARARGS, "Return (start, end) tuple of group."},
    {nullptr, nullptr, 0, nullptr}
};

int lstring_re_register_match_type(PyObject *submodule) {
    static PyType_Slot match_slots[] = {
        {Py_tp_new, (void*)Match_new},
        {Py_tp_init, (void*)Match_init},
        {Py_tp_dealloc, (void*)Match_dealloc},
        {Py_tp_repr, (void*)Match_repr},
        {Py_tp_methods, (void*)Match_methods},
        {Py_tp_getset, (void*)Match_getset},
        {Py_mp_subscript, (void*)Match_getitem},
        {0, nullptr}
    };

    static PyType_Spec match_spec = {
        "_lstring.re.Match",
        sizeof(MatchObject),
        0,
        Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,
        match_slots
    };

    PyObject *match_type = PyType_FromSpec(&match_spec);
    if (!match_type) return -1;
    if (PyModule_AddObject(submodule, "Match", match_type) < 0) {
        Py_DECREF(match_type);
        return -1;
    }
    return 0;
}
