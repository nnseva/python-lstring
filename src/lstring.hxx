#ifndef LSTRING_HXX
#define LSTRING_HXX

#include <Python.h>

// Forward declaration of Buffer to avoid cyclic include
class Buffer;

// Structure representing lstr object
typedef struct {
    PyObject_HEAD
    Buffer *buffer;
} LStrObject;

// Forward declaration: collapse helper for lstr
extern void lstr_collapse(LStrObject *self);

#endif // LSTRING_HXX
