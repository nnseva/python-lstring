#include <Python.h>
#include "lstring_re_match.hxx"
#include "lstring_re_regex.hxx"
#include "slice_buffer.hxx"
#include "lstring_utils.hxx"
#include <cppy/cppy.h>

// Use the same CharT choice as other regex components in this build.
using CharT = wchar_t;

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

// Helper: extract single group by index or name and return as L object
static PyObject*
extract_group_by_index_or_name(LStrMatchBuffer<CharT> *buf, PyObject *arg_obj) {
    LStrObject *where_lobj = reinterpret_cast<LStrObject*>(buf->where.get());
    LStrIteratorBuffer<CharT> begin_iter(where_lobj, 0);
    
    cppy::ptr lstr_type_ptr(get_string_lstr_type());
    if (!lstr_type_ptr) return nullptr;
    PyTypeObject *lstr_type = reinterpret_cast<PyTypeObject*>(lstr_type_ptr.get());
    
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
        
        LStrObject *result = (LStrObject*)PyType_GenericAlloc(lstr_type, 0);
        if (!result) return nullptr;
        result->buffer = new Slice1Buffer(buf->where.get(), start, end);
        return (PyObject*)result;
    }
    
    // Check if argument is a string (group name)
    // Accept both str and lstring.L
    LStrObject *name_lobj = nullptr;
    cppy::ptr temp_lobj;
    
    if (PyUnicode_Check(arg_obj)) {
        // Convert str to L
        temp_lobj = cppy::ptr(PyObject_CallFunctionObjArgs((PyObject*)lstr_type, arg_obj, nullptr));
        if (!temp_lobj) return nullptr;
        name_lobj = reinterpret_cast<LStrObject*>(temp_lobj.get());
    } else {
        // Check if it's already an L
        if (Py_TYPE(arg_obj) != lstr_type) {
            PyErr_SetString(PyExc_TypeError, "group() argument must be an integer, str, or lstring.L");
            return nullptr;
        }
        name_lobj = reinterpret_cast<LStrObject*>(arg_obj);
    }
    
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
    
    LStrObject *result = (LStrObject*)PyType_GenericAlloc(lstr_type, 0);
    if (!result) return nullptr;
    result->buffer = new Slice1Buffer(buf->where.get(), start, end);
    return (PyObject*)result;
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
        
        LStrObject *where_lobj = reinterpret_cast<LStrObject*>(buf->where.get());
        LStrIteratorBuffer<CharT> begin_iter(where_lobj, 0);
        Py_ssize_t start = begin_iter.distance_to(buf->results[0].first);
        Py_ssize_t end = begin_iter.distance_to(buf->results[0].second);
        
        cppy::ptr lstr_type_ptr(get_string_lstr_type());
        if (!lstr_type_ptr) return nullptr;
        PyTypeObject *lstr_type = reinterpret_cast<PyTypeObject*>(lstr_type_ptr.get());
        LStrObject *result = (LStrObject*)PyType_GenericAlloc(lstr_type, 0);
        if (!result) return nullptr;
        result->buffer = new Slice1Buffer(buf->where.get(), start, end);
        return (PyObject*)result;
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
    
    LStrObject *where_lobj = reinterpret_cast<LStrObject*>(buf->where.get());
    LStrIteratorBuffer<CharT> begin_iter(where_lobj, 0);
    
    cppy::ptr lstr_type_ptr(get_string_lstr_type());
    if (!lstr_type_ptr) return nullptr;
    PyTypeObject *lstr_type = reinterpret_cast<PyTypeObject*>(lstr_type_ptr.get());
    
    for (Py_ssize_t i = 0; i < num_capturing_groups; ++i) {
        Py_ssize_t group_index = i + 1;  // Skip group 0
        PyObject *group_value;
        
        if (!buf->results[group_index].matched) {
            group_value = default_value;
            Py_INCREF(default_value);
        } else {
            Py_ssize_t start = begin_iter.distance_to(buf->results[group_index].first);
            Py_ssize_t end = begin_iter.distance_to(buf->results[group_index].second);
            
            LStrObject *lobj = (LStrObject*)PyType_GenericAlloc(lstr_type, 0);
            if (!lobj) return nullptr;
            lobj->buffer = new Slice1Buffer(buf->where.get(), start, end);
            group_value = (PyObject*)lobj;
        }
        
        PyTuple_SET_ITEM(result_tuple.get(), i, group_value);
    }
    
    return result_tuple.release();
}

// expand(template)
static PyObject*
Match_expand(PyObject *self_obj, PyObject *args) {
    PyErr_SetString(PyExc_NotImplementedError, "Match.expand() not implemented yet");
    return nullptr;
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
    PyObject *group_arg = nullptr;
    if (!PyArg_ParseTuple(args, "|O", &group_arg)) return nullptr;

    if (!group_arg) {
        group_arg = PyLong_FromLong(0);
        if (!group_arg) return nullptr;
    } else {
        Py_INCREF(group_arg);
    }

    cppy::ptr group_arg_owner(group_arg);
    
    try {
        LStrObject *subject_lobj = (LStrObject*)(buf->where.get());
        LStrIteratorBuffer<CharT> begin_iter(subject_lobj, 0);
        
        // Handle integer index
        if (PyLong_Check(group_arg)) {
            int group_index = PyLong_AsLong(group_arg);
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
        
        // Handle string/L name
        cppy::ptr lstr_type_ptr(get_string_lstr_type());
        if (!lstr_type_ptr) return nullptr;
        PyTypeObject *lstr_type = reinterpret_cast<PyTypeObject*>(lstr_type_ptr.get());
        
        LStrObject *name_lobj = nullptr;
        cppy::ptr temp_lobj;
        
        if (PyUnicode_Check(group_arg)) {
            temp_lobj = cppy::ptr(PyObject_CallFunctionObjArgs((PyObject*)lstr_type, group_arg, nullptr));
            if (!temp_lobj) return nullptr;
            name_lobj = reinterpret_cast<LStrObject*>(temp_lobj.get());
        } else if (Py_TYPE(group_arg) == lstr_type) {
            name_lobj = reinterpret_cast<LStrObject*>(group_arg);
        } else {
            PyErr_SetString(PyExc_TypeError, "group index or name must be int, str, or L");
            return nullptr;
        }
        
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
    PyObject *group_arg = nullptr;
    if (!PyArg_ParseTuple(args, "|O", &group_arg)) return nullptr;

    if (!group_arg) {
        group_arg = PyLong_FromLong(0);
        if (!group_arg) return nullptr;
    } else {
        Py_INCREF(group_arg);
    }

    cppy::ptr group_arg_owner(group_arg);
    
    try {
        LStrObject *subject_lobj = (LStrObject*)(buf->where.get());
        LStrIteratorBuffer<CharT> begin_iter(subject_lobj, 0);
        
        // Handle integer index
        if (PyLong_Check(group_arg)) {
            int group_index = PyLong_AsLong(group_arg);
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
        
        // Handle string/L name
        cppy::ptr lstr_type_ptr(get_string_lstr_type());
        if (!lstr_type_ptr) return nullptr;
        PyTypeObject *lstr_type = reinterpret_cast<PyTypeObject*>(lstr_type_ptr.get());
        
        LStrObject *name_lobj = nullptr;
        cppy::ptr temp_lobj;
        
        if (PyUnicode_Check(group_arg)) {
            temp_lobj = cppy::ptr(PyObject_CallFunctionObjArgs((PyObject*)lstr_type, group_arg, nullptr));
            if (!temp_lobj) return nullptr;
            name_lobj = reinterpret_cast<LStrObject*>(temp_lobj.get());
        } else if (Py_TYPE(group_arg) == lstr_type) {
            name_lobj = reinterpret_cast<LStrObject*>(group_arg);
        } else {
            PyErr_SetString(PyExc_TypeError, "group index or name must be int, str, or L");
            return nullptr;
        }
        
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
    PyObject *group_arg = nullptr;
    if (!PyArg_ParseTuple(args, "|O", &group_arg)) return nullptr;

    if (!group_arg) {
        group_arg = PyLong_FromLong(0);
        if (!group_arg) return nullptr;
    } else {
        Py_INCREF(group_arg);
    }

    cppy::ptr group_arg_owner(group_arg);
    
    try {
        LStrObject *subject_lobj = (LStrObject*)(buf->where.get());
        LStrIteratorBuffer<CharT> begin_iter(subject_lobj, 0);
        
        // Handle integer index
        if (PyLong_Check(group_arg)) {
            int group_index = PyLong_AsLong(group_arg);
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
        
        // Handle string/L name
        cppy::ptr lstr_type_ptr(get_string_lstr_type());
        if (!lstr_type_ptr) return nullptr;
        PyTypeObject *lstr_type = reinterpret_cast<PyTypeObject*>(lstr_type_ptr.get());
        
        LStrObject *name_lobj = nullptr;
        cppy::ptr temp_lobj;
        
        if (PyUnicode_Check(group_arg)) {
            temp_lobj = cppy::ptr(PyObject_CallFunctionObjArgs((PyObject*)lstr_type, group_arg, nullptr));
            if (!temp_lobj) return nullptr;
            name_lobj = reinterpret_cast<LStrObject*>(temp_lobj.get());
        } else if (Py_TYPE(group_arg) == lstr_type) {
            name_lobj = reinterpret_cast<LStrObject*>(group_arg);
        } else {
            PyErr_SetString(PyExc_TypeError, "group index or name must be int, str, or L");
            return nullptr;
        }
        
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

        LStrObject *subject_lobj = (LStrObject*)(buf->where.get());
        LStrIteratorBuffer<CharT> begin_iter(subject_lobj, 0);
        Py_ssize_t start_pos = begin_iter.distance_to(buf->results[0].first);
        Py_ssize_t end_pos = begin_iter.distance_to(buf->results[0].second);
        
        // Get the matched string
        cppy::ptr lstr_type_ptr(get_string_lstr_type());
        if (!lstr_type_ptr) return nullptr;
        PyTypeObject *lstr_type = reinterpret_cast<PyTypeObject*>(lstr_type_ptr.get());
        
        LStrObject *match_lobj = (LStrObject*)PyType_GenericAlloc(lstr_type, 0);
        if (!match_lobj) return nullptr;
        match_lobj->buffer = new Slice1Buffer(buf->where.get(), start_pos, end_pos);
        
        // Convert to Python str for display
        cppy::ptr match_str(PyObject_Str((PyObject*)match_lobj));
        Py_DECREF(match_lobj);
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
    {"expand", (PyCFunction)Match_expand, METH_VARARGS, "Expand template with group contents (not implemented)."},
    {nullptr, nullptr, 0, nullptr}
};

int lstring_re_register_match_type(PyObject *submodule) {
    static PyType_Slot match_slots[] = {
        {Py_tp_dealloc, (void*)Match_dealloc},
        {Py_tp_repr, (void*)Match_repr},
        {Py_tp_methods, (void*)Match_methods},
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
