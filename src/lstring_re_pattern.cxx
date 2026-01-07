#include <Python.h>
#include "lstring_re_pattern.hxx"
#include "lstring_re_regex.hxx"
#include "lstring_utils.hxx"
#include "lstring_re_match.hxx"
#include "slice_buffer.hxx"
#include "tptr.hxx"
#include <cppy/cppy.h>
#include <boost/regex.hpp>

using CharT = Py_UCS4;

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

// Pattern.__new__(cls) - minimal object creation
PyObject* Pattern_new(PyTypeObject *type, PyObject *args, PyObject *kwds) {
    PatternObject *self = (PatternObject*)type->tp_alloc(type, 0);
    if (!self) return nullptr;
    self->buf = nullptr;
    self->match_factory = nullptr;
    return (PyObject*)self;
}

// Pattern.__init__(self, pattern: L, flags: int, Match: type)
int Pattern_init(PyObject *self_obj, PyObject *args, PyObject *kwds) {
    PatternObject *self = (PatternObject*)self_obj;
    PyObject *pattern_arg = nullptr;
    int flags = 0;
    PyObject *match_factory = nullptr;
    static char *kwlist[] = {(char*)"pattern", (char*)"flags", (char*)"Match", nullptr};
    
    if (!PyArg_ParseTupleAndKeywords(args, kwds, "OiO", kwlist, &pattern_arg, &flags, &match_factory)) return -1;

    // Verify that pattern is lstring.L
    tptr<PyTypeObject> LType(get_string_lstr_type());
    if (!LType) return -1;
    int is_instance = PyObject_IsInstance(pattern_arg, LType.ptr().get());
    if (is_instance == 0) {
        PyErr_SetString(PyExc_TypeError, "pattern must be lstring.L");
        return -1;
    } else if (is_instance < 0) {
        return -1;
    }

    // Create regex buffer
    try {
        LStrObject *pat = reinterpret_cast<LStrObject*>(pattern_arg);
        self->buf = new LStrRegexBuffer<CharT>(pat, flags);
    } catch (const std::exception &e) {
        PyErr_SetString(PyExc_RuntimeError, e.what());
        return -1;
    }

    // Verify that match_factory is a subclass of _lstring.re.Match
    cppy::ptr lmod(PyImport_ImportModule("_lstring"));
    if (!lmod) return -1;
    cppy::ptr re_sub(PyObject_GetAttrString(lmod.get(), "re"));
    if (!re_sub) return -1;
    cppy::ptr base_match_type(PyObject_GetAttrString(re_sub.get(), "Match"));
    if (!base_match_type) return -1;
    
    int is_subclass = PyObject_IsSubclass(match_factory, base_match_type.get());
    if (is_subclass == -1) {
        return -1;
    } else if (is_subclass == 0) {
        PyErr_SetString(PyExc_TypeError, "Match parameter must be a subclass of _lstring.re.Match");
        return -1;
    }
    
    // Store owned reference to match factory
    self->match_factory = cppy::incref(match_factory);

    return 0;
}

// Helper function to parse and validate subject argument from Pattern methods.
// Parses subject (must be lstring.L), pos, and endpos parameters.
// Returns tptr<LStrObject> holding the validated subject, or empty tptr on error.
static tptr<LStrObject> parse_subject_argument(PyObject *args, Py_ssize_t &pos, Py_ssize_t &endpos) {
    PyObject *subject = nullptr;
    PyObject *pos_obj = nullptr;
    PyObject *endpos_obj = nullptr;
    
    if (!PyArg_ParseTuple(args, "O|OO", &subject, &pos_obj, &endpos_obj)) return tptr<LStrObject>();

    // Verify that subject is lstring.L
    tptr<PyTypeObject> LType(get_string_lstr_type());
    if (!LType) return tptr<LStrObject>();
    int is_inst = PyObject_IsInstance(subject, LType.ptr().get());
    if (is_inst == 0) {
        PyErr_SetString(PyExc_TypeError, "subject must be lstring.L");
        return tptr<LStrObject>();
    } else if (is_inst < 0) {
        return tptr<LStrObject>();
    }
    tptr<LStrObject> subject_owner(subject, true); // take new ref

    // Parse pos parameter (default: 0)
    pos = 0;
    if (pos_obj && pos_obj != Py_None) {
        pos = PyLong_AsSsize_t(pos_obj);
        if (pos == -1 && PyErr_Occurred()) return tptr<LStrObject>();
        if (pos < 0) {
            PyErr_SetString(PyExc_ValueError, "pos must be non-negative");
            return tptr<LStrObject>();
        }
    }

    // Parse endpos parameter (default: length of subject)
    Py_ssize_t subject_len = subject_owner->buffer->length();
    endpos = subject_len;
    if (endpos_obj && endpos_obj != Py_None) {
        endpos = PyLong_AsSsize_t(endpos_obj);
        if (endpos == -1 && PyErr_Occurred()) return tptr<LStrObject>();
        if (endpos < 0) {
            PyErr_SetString(PyExc_ValueError, "endpos must be non-negative");
            return tptr<LStrObject>();
        }
    }

    // Clamp pos and endpos to valid range
    if (pos > subject_len) pos = subject_len;
    if (endpos > subject_len) endpos = subject_len;
    if (endpos < pos) endpos = pos;

    return subject_owner;
}

// Create a new Match instance using the provided factory with pattern and subject.
// Returns tptr<MatchObject> with the new Match instance, or empty tptr on failure.
tptr<MatchObject> lstring_re_create_match(PyObject *match_factory, PyObject *pattern, PyObject *subject, Py_ssize_t pos, Py_ssize_t endpos) {
    cppy::ptr args(Py_BuildValue("(OOnn)", pattern, subject, pos, endpos));
    if (!args) return tptr<MatchObject>();
    
    return PyObject_CallObject(match_factory, args.get());
}


// Stub: Pattern.match(subject, pos=0, endpos=sys.maxsize)
static PyObject* Pattern_match(PyObject *self_obj, PyObject *args) {
    PatternObject *self = (PatternObject*)self_obj;
    if (!self->buf) {
        PyErr_SetString(PyExc_RuntimeError, "invalid Pattern (no compiled regex)");
        return nullptr;
    }

    Py_ssize_t pos, endpos;
    tptr<LStrObject> subject_owner = parse_subject_argument(args, pos, endpos);
    if (!subject_owner) return nullptr;

    tptr<MatchObject> match_owner = lstring_re_create_match(self->match_factory, self_obj, subject_owner.ptr().get(), pos, endpos);
    if (!match_owner) return nullptr;
    
    auto *matchbuf = reinterpret_cast<LStrMatchBuffer<CharT>*>(match_owner->matchbuf);

    bool found = false;
    try {
        LStrObject *lobj = subject_owner.get();
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

    return match_owner.ptr().release();
}

// Stub: Pattern.search(subject, pos=0, endpos=sys.maxsize)
static PyObject* Pattern_search(PyObject *self_obj, PyObject *args) {
    PatternObject *self = (PatternObject*)self_obj;
    if (!self->buf) {
        PyErr_SetString(PyExc_RuntimeError, "invalid Pattern (no compiled regex)");
        return nullptr;
    }

    Py_ssize_t pos, endpos;
    tptr<LStrObject> subject_owner = parse_subject_argument(args, pos, endpos);
    if (!subject_owner) return nullptr;

    tptr<MatchObject> match_owner = lstring_re_create_match(self->match_factory, self_obj, subject_owner.ptr().get(), pos, endpos);
    if (!match_owner) return nullptr;
    
    auto *matchbuf = reinterpret_cast<LStrMatchBuffer<CharT>*>(match_owner->matchbuf);

    bool found = false;
    try {
        LStrObject *lobj = subject_owner.get();
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

    return match_owner.ptr().release();
}

// Stub: Pattern.fullmatch(subject, pos=0, endpos=sys.maxsize)
static PyObject* Pattern_fullmatch(PyObject *self_obj, PyObject *args) {
    PatternObject *self = (PatternObject*)self_obj;
    if (!self->buf) {
        PyErr_SetString(PyExc_RuntimeError, "invalid Pattern (no compiled regex)");
        return nullptr;
    }

    Py_ssize_t pos, endpos;
    tptr<LStrObject> subject_owner = parse_subject_argument(args, pos, endpos);
    if (!subject_owner) return nullptr;

    tptr<MatchObject> match_owner = lstring_re_create_match(self->match_factory, self_obj, subject_owner.ptr().get(), pos, endpos);
    if (!match_owner) return nullptr;
    
    auto *matchbuf = reinterpret_cast<LStrMatchBuffer<CharT>*>(match_owner->matchbuf);

    bool found = false;
    try {
        LStrObject *lobj = subject_owner.get();
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

    return match_owner.ptr().release();
}

PyMethodDef Pattern_methods[] = {
    {"match", (PyCFunction)Pattern_match, METH_VARARGS, "Pattern.match(subject[, pos[, endpos]]) -> Match or None."},
    {"fullmatch", (PyCFunction)Pattern_fullmatch, METH_VARARGS, "Pattern.fullmatch(subject[, pos[, endpos]]) -> Match or None."},
    {"search", (PyCFunction)Pattern_search, METH_VARARGS, "Pattern.search(subject[, pos[, endpos]]) -> Match or None."},
    {nullptr, nullptr, 0, nullptr}
};

int lstring_re_register_pattern_type(PyObject *submodule) {
    static PyType_Slot pattern_slots[] = {
        {Py_tp_new, (void*)Pattern_new},
        {Py_tp_init, (void*)Pattern_init},
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
        cppy::decref(pattern_type);
        return -1;
    }
    return 0;
}
