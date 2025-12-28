#include <Python.h>
#include "lstring_re_pattern.hxx"
#include "lstring_re_regex.hxx"
#include "lstring_utils.hxx"
#include "lstring_re_match.hxx"
#include "slice_buffer.hxx"
#include <cppy/cppy.h>
#include <boost/regex.hpp>

using CharT = wchar_t; // keep consistent with module placeholder

// Declaration of PatternObject used by PyType_Spec
struct PatternObject {
    PyObject_HEAD
    LStrRegexBuffer<CharT> *buf;
    PyObject *match_factory; // Factory (class or callable) to create Match instances
};

// Free PatternObject
void Pattern_dealloc(PyObject *self_obj) {
    PatternObject *self = (PatternObject*)self_obj;
    if (self->buf) {
        delete self->buf;
        self->buf = nullptr;
    }
    Py_XDECREF(self->match_factory);
    Py_TYPE(self)->tp_free(self_obj);
}

// Pattern.__new__(cls, pattern: L|str, flags: int=0, Match=None)
PyObject* Pattern_new(PyTypeObject *type, PyObject *args, PyObject *kwds) {
    PyObject *pattern_arg = nullptr;
    int flags = 0;
    PyObject *match_factory = nullptr;
    static char *kwlist[] = {(char*)"pattern", (char*)"flags", (char*)"Match", nullptr};
    
    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O|iO", kwlist, &pattern_arg, &flags, &match_factory)) return nullptr;

    PatternObject *self = (PatternObject*)type->tp_alloc(type, 0);
    if (!self) return nullptr;
    self->buf = nullptr;
    self->match_factory = nullptr;
    cppy::ptr self_owner((PyObject*)self);
    cppy::ptr owned_pat;

    if (PyUnicode_Check(pattern_arg)) {
        PyObject *tmp = make_lstr_from_pystr(pattern_arg);
        if (!tmp) return nullptr;
        owned_pat = cppy::ptr(tmp);
    } else {
        cppy::ptr LType(get_string_lstr_type());
        if (!LType) return nullptr;
        int is_instance = PyObject_IsInstance(pattern_arg, LType.get());
        if (is_instance == 1) {
            owned_pat = cppy::ptr(pattern_arg, true);
        } else if (is_instance == 0) {
            PyErr_SetString(PyExc_TypeError, "pattern must be lstring.L or str");
            return nullptr;
        } else {
            return nullptr;
        }
    }

    try {
        LStrObject *pat = reinterpret_cast<LStrObject*>(owned_pat.get());
        self->buf = new LStrRegexBuffer<CharT>(pat, flags);
    } catch (const std::exception &e) {
        PyErr_SetString(PyExc_RuntimeError, e.what());
        return nullptr;
    }

    // Set match_factory: use provided or default to lstring.re.Match
    if (match_factory && match_factory != Py_None) {
        // Verify that match_factory is a subclass of _lstring.re.Match
        cppy::ptr lmod(PyImport_ImportModule("_lstring"));
        if (!lmod) return nullptr;
        cppy::ptr re_sub(PyObject_GetAttrString(lmod.get(), "re"));
        if (!re_sub) return nullptr;
        cppy::ptr base_match_type(PyObject_GetAttrString(re_sub.get(), "Match"));
        if (!base_match_type) return nullptr;
        
        int is_subclass = PyObject_IsSubclass(match_factory, base_match_type.get());
        if (is_subclass == -1) {
            return nullptr;
        } else if (is_subclass == 0) {
            PyErr_SetString(PyExc_TypeError, "Match parameter must be a subclass of _lstring.re.Match");
            return nullptr;
        }
        
        Py_INCREF(match_factory);
        self->match_factory = match_factory;
    } else {
        // Default: use lstring.re.Match (currently points to _lstring.re.Match)
        cppy::ptr lmod(PyImport_ImportModule("lstring"));
        if (!lmod) return nullptr;
        cppy::ptr re_sub(PyObject_GetAttrString(lmod.get(), "re"));
        if (!re_sub) return nullptr;
        cppy::ptr match_type(PyObject_GetAttrString(re_sub.get(), "Match"));
        if (!match_type) return nullptr;
        
        self->match_factory = match_type.release();
    }

    return self_owner.release();
}

// Helper function to parse and validate subject argument from Pattern methods.
// Converts Python str to lstring.L if needed and stores ownership in subject_owner.
// Parses optional pos and endpos parameters (default: 0 and subject length).
// Returns the validated subject as PyObject* (pointing to lstring.L), or nullptr on error.
static PyObject* parse_subject_argument(PyObject *args, cppy::ptr &subject_owner, Py_ssize_t &pos, Py_ssize_t &endpos) {
    PyObject *subject = nullptr;
    PyObject *pos_obj = nullptr;
    PyObject *endpos_obj = nullptr;
    
    if (!PyArg_ParseTuple(args, "O|OO", &subject, &pos_obj, &endpos_obj)) return nullptr;

    if (PyUnicode_Check(subject)) {
        PyObject *tmp = make_lstr_from_pystr(subject);
        if (!tmp) return nullptr;
        subject_owner = cppy::ptr(tmp); // owns temporary
        subject = subject_owner.get();
    } else {
        cppy::ptr LType(get_string_lstr_type());
        if (!LType) return nullptr;
        int is_inst = PyObject_IsInstance(subject, LType.get());
        if (is_inst == 0) {
            PyErr_SetString(PyExc_TypeError, "subject must be lstring.L or str");
            return nullptr;
        } else if (is_inst < 0) {
            return nullptr;
        }
        subject_owner = cppy::ptr(subject, true); // take new ref
    }

    // Parse pos parameter (default: 0)
    pos = 0;
    if (pos_obj && pos_obj != Py_None) {
        pos = PyLong_AsSsize_t(pos_obj);
        if (pos == -1 && PyErr_Occurred()) return nullptr;
        if (pos < 0) {
            PyErr_SetString(PyExc_ValueError, "pos must be non-negative");
            return nullptr;
        }
    }

    // Parse endpos parameter (default: length of subject)
    LStrObject *lobj = reinterpret_cast<LStrObject*>(subject);
    Py_ssize_t subject_len = lobj->buffer->length();
    endpos = subject_len;
    if (endpos_obj && endpos_obj != Py_None) {
        endpos = PyLong_AsSsize_t(endpos_obj);
        if (endpos == -1 && PyErr_Occurred()) return nullptr;
        if (endpos < 0) {
            PyErr_SetString(PyExc_ValueError, "endpos must be non-negative");
            return nullptr;
        }
    }

    // Clamp pos and endpos to valid range
    if (pos > subject_len) pos = subject_len;
    if (endpos > subject_len) endpos = subject_len;
    if (endpos < pos) endpos = pos;

    return subject;
}

// Create a new Match instance using the provided factory with pattern and subject.
// Returns a new reference. On failure the nullptr is returned.
PyObject *lstring_re_create_match(PyObject *match_factory, PyObject *pattern, PyObject *subject) {
    cppy::ptr args(Py_BuildValue("(OO)", pattern, subject));
    if (!args) return nullptr;
    
    cppy::ptr obj = PyObject_CallObject(match_factory, args.get());
    if (!obj) return nullptr;
    
    return obj.release();
}


// Stub: Pattern.match(subject, pos=0, endpos=sys.maxsize)
static PyObject* Pattern_match(PyObject *self_obj, PyObject *args) {
    PatternObject *self = (PatternObject*)self_obj;
    if (!self->buf) {
        PyErr_SetString(PyExc_RuntimeError, "invalid Pattern (no compiled regex)");
        return nullptr;
    }

    cppy::ptr subject_owner;
    Py_ssize_t pos, endpos;
    PyObject *subject = parse_subject_argument(args, subject_owner, pos, endpos);
    if (!subject) return nullptr;

    cppy::ptr match_owner = lstring_re_create_match(self->match_factory, self_obj, subject);
    if (!match_owner) return nullptr;
    
    MatchObject *match_obj = (MatchObject*)(match_owner.get());
    auto *matchbuf = reinterpret_cast<LStrMatchBuffer<CharT>*>(match_obj->matchbuf);

    LStrObject *lobj = (LStrObject*)subject;
    bool found = false;
    try {
        LStrIteratorBuffer<CharT> begin(lobj, pos);
        LStrIteratorBuffer<CharT> end(lobj, endpos);
        found = boost::regex_search(begin, end, matchbuf->results, self->buf->re, boost::match_continuous);
    } catch (const std::exception &e) {
        PyErr_SetString(PyExc_RuntimeError, e.what());
        return nullptr;
    }

    if (!found) {
        Py_RETURN_NONE;
    }

    return match_owner.release();
}

// Stub: Pattern.search(subject, pos=0, endpos=sys.maxsize)
static PyObject* Pattern_search(PyObject *self_obj, PyObject *args) {
    PatternObject *self = (PatternObject*)self_obj;
    if (!self->buf) {
        PyErr_SetString(PyExc_RuntimeError, "invalid Pattern (no compiled regex)");
        return nullptr;
    }

    cppy::ptr subject_owner;
    Py_ssize_t pos, endpos;
    PyObject *subject = parse_subject_argument(args, subject_owner, pos, endpos);
    if (!subject) return nullptr;

    cppy::ptr match_owner = lstring_re_create_match(self->match_factory, self_obj, subject);
    if (!match_owner) return nullptr;
    
    MatchObject *match_obj = (MatchObject*)(match_owner.get());
    auto *matchbuf = reinterpret_cast<LStrMatchBuffer<CharT>*>(match_obj->matchbuf);

    LStrObject *lobj = (LStrObject*)subject;
    bool found = false;
    try {
        LStrIteratorBuffer<CharT> begin(lobj, pos);
        LStrIteratorBuffer<CharT> end(lobj, endpos);
        found = boost::regex_search(begin, end, matchbuf->results, self->buf->re);
    } catch (const std::exception &e) {
        PyErr_SetString(PyExc_RuntimeError, e.what());
        return nullptr;
    }

    if (!found) {
        Py_RETURN_NONE;
    }

    return match_owner.release();
}

// Stub: Pattern.fullmatch(subject, pos=0, endpos=sys.maxsize)
static PyObject* Pattern_fullmatch(PyObject *self_obj, PyObject *args) {
    PatternObject *self = (PatternObject*)self_obj;
    if (!self->buf) {
        PyErr_SetString(PyExc_RuntimeError, "invalid Pattern (no compiled regex)");
        return nullptr;
    }

    cppy::ptr subject_owner;
    Py_ssize_t pos, endpos;
    PyObject *subject = parse_subject_argument(args, subject_owner, pos, endpos);
    if (!subject) return nullptr;

    cppy::ptr match_owner = lstring_re_create_match(self->match_factory, self_obj, subject);
    if (!match_owner) return nullptr;
    
    MatchObject *match_obj = (MatchObject*)(match_owner.get());
    auto *matchbuf = reinterpret_cast<LStrMatchBuffer<CharT>*>(match_obj->matchbuf);

    LStrObject *lobj = (LStrObject*)subject;
    bool found = false;
    try {
        LStrIteratorBuffer<CharT> begin(lobj, pos);
        LStrIteratorBuffer<CharT> end(lobj, endpos);
        found = boost::regex_match(begin, end, matchbuf->results, self->buf->re);
    } catch (const std::exception &e) {
        PyErr_SetString(PyExc_RuntimeError, e.what());
        return nullptr;
    }

    if (!found) {
        Py_RETURN_NONE;
    }

    return match_owner.release();
}

// Pattern.findall(subject, pos=0, endpos=sys.maxsize) -> list
static PyObject* Pattern_findall(PyObject *self_obj, PyObject *args) {
    PatternObject *self = (PatternObject*)self_obj;
    if (!self->buf) {
        PyErr_SetString(PyExc_RuntimeError, "invalid Pattern (no compiled regex)");
        return nullptr;
    }

    cppy::ptr subject_owner;
    Py_ssize_t pos, endpos;
    PyObject *subject = parse_subject_argument(args, subject_owner, pos, endpos);
    if (!subject) return nullptr;

    cppy::ptr result_list(PyList_New(0));
    if (!result_list) return nullptr;

    LStrObject *lobj = (LStrObject*)subject;
    LStrIteratorBuffer<CharT> search_start(lobj, pos);
    LStrIteratorBuffer<CharT> search_end(lobj, endpos);

    cppy::ptr lstr_type_ptr(get_string_lstr_type());
    if (!lstr_type_ptr) return nullptr;
    PyTypeObject *lstr_type = reinterpret_cast<PyTypeObject*>(lstr_type_ptr.get());

    try {
        boost::match_results<LStrIteratorBuffer<CharT>> results;
        auto current = search_start;
        
        while (boost::regex_search(current, search_end, results, self->buf->re)) {
            Py_ssize_t num_groups = static_cast<Py_ssize_t>(results.size());
            
            // Determine what to add based on number of capturing groups
            if (num_groups <= 1) {
                // No capturing groups: return full match (group 0)
                if (results[0].matched) {
                    LStrIteratorBuffer<CharT> begin_iter(lobj, 0);
                    Py_ssize_t start = begin_iter.distance_to(results[0].first);
                    Py_ssize_t end = begin_iter.distance_to(results[0].second);
                    
                    LStrObject *match_lobj = (LStrObject*)PyType_GenericAlloc(lstr_type, 0);
                    if (!match_lobj) return nullptr;
                    match_lobj->buffer = new Slice1Buffer(subject, start, end);
                    
                    if (PyList_Append(result_list.get(), (PyObject*)match_lobj) < 0) {
                        Py_DECREF(match_lobj);
                        return nullptr;
                    }
                    Py_DECREF(match_lobj);
                }
            } else if (num_groups == 2) {
                // One capturing group: return group 1
                if (results[1].matched) {
                    LStrIteratorBuffer<CharT> begin_iter(lobj, 0);
                    Py_ssize_t start = begin_iter.distance_to(results[1].first);
                    Py_ssize_t end = begin_iter.distance_to(results[1].second);
                    
                    LStrObject *group_lobj = (LStrObject*)PyType_GenericAlloc(lstr_type, 0);
                    if (!group_lobj) return nullptr;
                    group_lobj->buffer = new Slice1Buffer(subject, start, end);
                    
                    if (PyList_Append(result_list.get(), (PyObject*)group_lobj) < 0) {
                        Py_DECREF(group_lobj);
                        return nullptr;
                    }
                    Py_DECREF(group_lobj);
                } else {
                    // Unmatched group
                    if (PyList_Append(result_list.get(), Py_None) < 0) {
                        return nullptr;
                    }
                }
            } else {
                // Multiple capturing groups: return tuple of groups (excluding group 0)
                cppy::ptr tuple(PyTuple_New(num_groups - 1));
                if (!tuple) return nullptr;
                
                LStrIteratorBuffer<CharT> begin_iter(lobj, 0);
                for (Py_ssize_t i = 1; i < num_groups; ++i) {
                    PyObject *group_value;
                    if (results[i].matched) {
                        Py_ssize_t start = begin_iter.distance_to(results[i].first);
                        Py_ssize_t end = begin_iter.distance_to(results[i].second);
                        
                        LStrObject *group_lobj = (LStrObject*)PyType_GenericAlloc(lstr_type, 0);
                        if (!group_lobj) return nullptr;
                        group_lobj->buffer = new Slice1Buffer(subject, start, end);
                        group_value = (PyObject*)group_lobj;
                    } else {
                        group_value = Py_None;
                        Py_INCREF(Py_None);
                    }
                    PyTuple_SET_ITEM(tuple.get(), i - 1, group_value);
                }
                
                if (PyList_Append(result_list.get(), tuple.get()) < 0) {
                    return nullptr;
                }
            }
            
            // Move to next position
            if (results[0].first == results[0].second) {
                // Empty match, advance by one to avoid infinite loop
                if (current == search_end) break;
                ++current;
            } else {
                current = results[0].second;
            }
        }
    } catch (const std::exception &e) {
        PyErr_SetString(PyExc_RuntimeError, e.what());
        return nullptr;
    }

    return result_list.release();
}

// Pattern.finditer(subject, pos=0, endpos=sys.maxsize) -> iterator
static PyObject* Pattern_finditer(PyObject *self_obj, PyObject *args) {
    PatternObject *self = (PatternObject*)self_obj;
    if (!self->buf) {
        PyErr_SetString(PyExc_RuntimeError, "invalid Pattern (no compiled regex)");
        return nullptr;
    }

    cppy::ptr subject_owner;
    Py_ssize_t pos, endpos;
    PyObject *subject = parse_subject_argument(args, subject_owner, pos, endpos);
    if (!subject) return nullptr;

    // For simplicity, collect all matches into a list and return iter()
    // A proper implementation would create a custom iterator type
    cppy::ptr result_list(PyList_New(0));
    if (!result_list) return nullptr;

    LStrObject *lobj = (LStrObject*)subject;
    LStrIteratorBuffer<CharT> search_start(lobj, pos);
    LStrIteratorBuffer<CharT> search_end(lobj, endpos);

    try {
        boost::match_results<LStrIteratorBuffer<CharT>> results;
        auto current = search_start;
        
        while (boost::regex_search(current, search_end, results, self->buf->re)) {
            // Create a Match object for this result
            cppy::ptr match_owner = lstring_re_create_match(self->match_factory, self_obj, subject);
            if (!match_owner) return nullptr;
            
            MatchObject *match_obj = (MatchObject*)(match_owner.get());
            auto *matchbuf = reinterpret_cast<LStrMatchBuffer<CharT>*>(match_obj->matchbuf);
            matchbuf->results = results;
            
            if (PyList_Append(result_list.get(), match_owner.get()) < 0) {
                return nullptr;
            }
            
            // Move to next position
            if (results[0].first == results[0].second) {
                // Empty match, advance by one to avoid infinite loop
                if (current == search_end) break;
                ++current;
            } else {
                current = results[0].second;
            }
        }
    } catch (const std::exception &e) {
        PyErr_SetString(PyExc_RuntimeError, e.what());
        return nullptr;
    }

    // Return an iterator over the list
    return PyObject_GetIter(result_list.get());
}

// Stub: Pattern.sub(repl, subject, count=0)
static PyObject* Pattern_sub(PyObject *self_obj, PyObject *args) {
    PyErr_SetString(PyExc_NotImplementedError, "Pattern.sub() not implemented yet");
    return nullptr;
}

// Stub: Pattern.subn(repl, subject, count=0)
static PyObject* Pattern_subn(PyObject *self_obj, PyObject *args) {
    PyErr_SetString(PyExc_NotImplementedError, "Pattern.subn() not implemented yet");
    return nullptr;
}

// Pattern.split(subject, maxsplit=0) -> list
static PyObject* Pattern_split(PyObject *self_obj, PyObject *args) {
    PatternObject *self = (PatternObject*)self_obj;
    if (!self->buf) {
        PyErr_SetString(PyExc_RuntimeError, "invalid Pattern (no compiled regex)");
        return nullptr;
    }

    PyObject *subject_arg = nullptr;
    int maxsplit = 0;
    if (!PyArg_ParseTuple(args, "O|i", &subject_arg, &maxsplit)) return nullptr;

    cppy::ptr subject_owner;
    if (PyUnicode_Check(subject_arg)) {
        PyObject *tmp = make_lstr_from_pystr(subject_arg);
        if (!tmp) return nullptr;
        subject_owner = cppy::ptr(tmp);
        subject_arg = subject_owner.get();
    } else {
        cppy::ptr LType(get_string_lstr_type());
        if (!LType) return nullptr;
        int is_inst = PyObject_IsInstance(subject_arg, LType.get());
        if (is_inst == 0) {
            PyErr_SetString(PyExc_TypeError, "subject must be lstring.L or str");
            return nullptr;
        } else if (is_inst < 0) {
            return nullptr;
        }
        subject_owner = cppy::ptr(subject_arg, true);
    }

    cppy::ptr result_list(PyList_New(0));
    if (!result_list) return nullptr;

    LStrObject *lobj = (LStrObject*)subject_arg;
    Py_ssize_t subject_len = lobj->buffer->length();
    
    cppy::ptr lstr_type_ptr(get_string_lstr_type());
    if (!lstr_type_ptr) return nullptr;
    PyTypeObject *lstr_type = reinterpret_cast<PyTypeObject*>(lstr_type_ptr.get());

    try {
        LStrIteratorBuffer<CharT> search_start(lobj, 0);
        LStrIteratorBuffer<CharT> search_end(lobj, subject_len);
        boost::match_results<LStrIteratorBuffer<CharT>> results;
        
        Py_ssize_t last_end = 0;
        int split_count = 0;
        auto current = search_start;
        
        while ((maxsplit == 0 || split_count < maxsplit) && 
               boost::regex_search(current, search_end, results, self->buf->re)) {
            
            LStrIteratorBuffer<CharT> begin_iter(lobj, 0);
            Py_ssize_t match_start = begin_iter.distance_to(results[0].first);
            Py_ssize_t match_end = begin_iter.distance_to(results[0].second);
            
            // Add the part before the match
            if (match_start >= last_end) {
                LStrObject *part = (LStrObject*)PyType_GenericAlloc(lstr_type, 0);
                if (!part) return nullptr;
                part->buffer = new Slice1Buffer(subject_arg, last_end, match_start);
                
                if (PyList_Append(result_list.get(), (PyObject*)part) < 0) {
                    Py_DECREF(part);
                    return nullptr;
                }
                Py_DECREF(part);
            }
            
            // Add capturing groups to result
            Py_ssize_t num_groups = static_cast<Py_ssize_t>(results.size());
            for (Py_ssize_t i = 1; i < num_groups; ++i) {
                if (results[i].matched) {
                    Py_ssize_t group_start = begin_iter.distance_to(results[i].first);
                    Py_ssize_t group_end = begin_iter.distance_to(results[i].second);
                    
                    LStrObject *group_lobj = (LStrObject*)PyType_GenericAlloc(lstr_type, 0);
                    if (!group_lobj) return nullptr;
                    group_lobj->buffer = new Slice1Buffer(subject_arg, group_start, group_end);
                    
                    if (PyList_Append(result_list.get(), (PyObject*)group_lobj) < 0) {
                        Py_DECREF(group_lobj);
                        return nullptr;
                    }
                    Py_DECREF(group_lobj);
                } else {
                    if (PyList_Append(result_list.get(), Py_None) < 0) {
                        return nullptr;
                    }
                }
            }
            
            last_end = match_end;
            split_count++;
            
            // Move to next position
            if (results[0].first == results[0].second) {
                // Empty match, advance by one to avoid infinite loop
                if (current == search_end) break;
                ++current;
                last_end++;
            } else {
                current = results[0].second;
            }
        }
        
        // Add the remaining part after the last match
        if (last_end <= subject_len) {
            LStrObject *part = (LStrObject*)PyType_GenericAlloc(lstr_type, 0);
            if (!part) return nullptr;
            part->buffer = new Slice1Buffer(subject_arg, last_end, subject_len);
            
            if (PyList_Append(result_list.get(), (PyObject*)part) < 0) {
                Py_DECREF(part);
                return nullptr;
            }
            Py_DECREF(part);
        }
        
    } catch (const std::exception &e) {
        PyErr_SetString(PyExc_RuntimeError, e.what());
        return nullptr;
    }

    return result_list.release();
}

PyMethodDef Pattern_methods[] = {
    {"match", (PyCFunction)Pattern_match, METH_VARARGS, "Pattern.match(subject[, pos[, endpos]]) -> Match or None."},
    {"fullmatch", (PyCFunction)Pattern_fullmatch, METH_VARARGS, "Pattern.fullmatch(subject[, pos[, endpos]]) -> Match or None."},
    {"search", (PyCFunction)Pattern_search, METH_VARARGS, "Pattern.search(subject[, pos[, endpos]]) -> Match or None."},
    {"findall", (PyCFunction)Pattern_findall, METH_VARARGS, "Pattern.findall(subject[, pos[, endpos]]) -> list (stub)."},
    {"finditer", (PyCFunction)Pattern_finditer, METH_VARARGS, "Pattern.finditer(subject[, pos[, endpos]]) -> iterator (stub)."},
    {"sub", (PyCFunction)Pattern_sub, METH_VARARGS, "Pattern.sub(repl, subject[, count]) -> str (stub)."},
    {"subn", (PyCFunction)Pattern_subn, METH_VARARGS, "Pattern.subn(repl, subject[, count]) -> (str, n) (stub)."},
    {"split", (PyCFunction)Pattern_split, METH_VARARGS, "Pattern.split(subject[, maxsplit]) -> list (stub)."},
    {nullptr, nullptr, 0, nullptr}
};

int lstring_re_register_pattern_type(PyObject *submodule) {
    static PyType_Slot pattern_slots[] = {
        {Py_tp_new, (void*)Pattern_new},
        {Py_tp_dealloc, (void*)Pattern_dealloc},
        {Py_tp_methods, (void*)Pattern_methods},
        {0, nullptr}
    };

    static PyType_Spec pattern_spec = {
        "_lstring.re.Pattern",
        sizeof(PatternObject),
        0,
        Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,
        pattern_slots
    };

    PyObject *pattern_type = PyType_FromSpec(&pattern_spec);
    if (!pattern_type) return -1;
    if (PyModule_AddObject(submodule, "Pattern", pattern_type) < 0) {
        Py_DECREF(pattern_type);
        return -1;
    }
    return 0;
}
