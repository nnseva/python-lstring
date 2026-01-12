#include <Python.h>

#include "_lstring.hxx"
#include "join_buffer.hxx"

static inline bool is_join_buffer(const LStrObject* obj) {
    return obj && obj->buffer && obj->buffer->is_a(JoinBuffer::buffer_class_id);
}

static inline const JoinBuffer* as_join_buffer(const LStrObject* obj) {
    return static_cast<const JoinBuffer*>(obj->buffer);
}

static inline Py_ssize_t lstr_height(const LStrObject* obj) {
    if (!obj || !obj->buffer) return 1;
    if (is_join_buffer(obj)) return as_join_buffer(obj)->height();
    return 1;
}

static tptr<LStrObject> make_join_lstr(PyTypeObject* type, PyObject* left, PyObject* right) {
    tptr<LStrObject> result((LStrObject*)type->tp_alloc(type, 0));
    if (!result) return {};

    try {
        result->buffer = new JoinBuffer(left, right);
    } catch (const std::exception &e) {
        PyErr_SetString(PyExc_RuntimeError, e.what());
        return {};
    } catch (...) {
        PyErr_SetString(PyExc_RuntimeError, "JoinBuffer allocation failed");
        return {};
    }

    return result;
}

static tptr<LStrObject> rotate_left(PyTypeObject* type, const tptr<LStrObject>& x) {
    // x = Join(a, y), y = Join(b, c)  =>  Join(Join(a,b), c)
    const JoinBuffer* jx = as_join_buffer(x.get());
    tptr<LStrObject> a(jx->left(), true);
    tptr<LStrObject> y(jx->right(), true);
    const JoinBuffer* jy = as_join_buffer(y.get());
    tptr<LStrObject> b(jy->left(), true);
    tptr<LStrObject> c(jy->right(), true);

    tptr<LStrObject> ab = make_join_lstr(type, a.ptr().get(), b.ptr().get());
    if (!ab) return {};
    return make_join_lstr(type, ab.ptr().get(), c.ptr().get());
}

static tptr<LStrObject> rotate_right(PyTypeObject* type, const tptr<LStrObject>& y) {
    // y = Join(x, c), x = Join(a, b)  =>  Join(a, Join(b,c))
    const JoinBuffer* jy = as_join_buffer(y.get());
    tptr<LStrObject> x(jy->left(), true);
    tptr<LStrObject> c(jy->right(), true);
    const JoinBuffer* jx = as_join_buffer(x.get());
    tptr<LStrObject> a(jx->left(), true);
    tptr<LStrObject> b(jx->right(), true);

    tptr<LStrObject> bc = make_join_lstr(type, b.ptr().get(), c.ptr().get());
    if (!bc) return {};
    return make_join_lstr(type, a.ptr().get(), bc.ptr().get());
}

static tptr<LStrObject> rebalance_join(PyTypeObject* type, const tptr<LStrObject>& node) {
    const JoinBuffer* jn = as_join_buffer(node.get());
    tptr<LStrObject> left(jn->left(), true);
    tptr<LStrObject> right(jn->right(), true);

    Py_ssize_t hl = lstr_height(left.get());
    Py_ssize_t hr = lstr_height(right.get());

    Py_ssize_t balance = hl - hr;
    if (balance > 1) {
        // Left heavy
        if (is_join_buffer(left.get())) {
            const JoinBuffer* jl = as_join_buffer(left.get());
            tptr<LStrObject> ll(jl->left(), true);
            tptr<LStrObject> lr(jl->right(), true);
            if (lstr_height(lr.get()) > lstr_height(ll.get())) {
                // LR case: rotate left on left child
                tptr<LStrObject> new_left = rotate_left(type, left);
                if (!new_left) return {};
                tptr<LStrObject> tmp = make_join_lstr(type, new_left.ptr().get(), right.ptr().get());
                if (!tmp) return {};
                return rotate_right(type, tmp);
            }
        }
        // LL case
        return rotate_right(type, node);
    }

    if (balance < -1) {
        // Right heavy
        if (is_join_buffer(right.get())) {
            const JoinBuffer* jr = as_join_buffer(right.get());
            tptr<LStrObject> rl(jr->left(), true);
            tptr<LStrObject> rr(jr->right(), true);
            if (lstr_height(rl.get()) > lstr_height(rr.get())) {
                // RL case: rotate right on right child
                tptr<LStrObject> new_right = rotate_right(type, right);
                if (!new_right) return {};
                tptr<LStrObject> tmp = make_join_lstr(type, left.ptr().get(), new_right.ptr().get());
                if (!tmp) return {};
                return rotate_left(type, tmp);
            }
        }
        // RR case
        return rotate_left(type, node);
    }

    return node;
}

tptr<LStrObject> concat_balanced(PyTypeObject* type, const tptr<LStrObject>& left, const tptr<LStrObject>& right) {
    Py_ssize_t hl = lstr_height(left.get());
    Py_ssize_t hr = lstr_height(right.get());

    if (hl > hr + 1) {
        // Left tree is taller; descend on its right spine.
        const JoinBuffer* jl = as_join_buffer(left.get());
        tptr<LStrObject> a(jl->left(), true);
        tptr<LStrObject> b(jl->right(), true);
        tptr<LStrObject> new_right = concat_balanced(type, b, right);
        if (!new_right) return {};
        tptr<LStrObject> node = make_join_lstr(type, a.ptr().get(), new_right.ptr().get());
        if (!node) return {};
        return rebalance_join(type, node);
    }

    if (hr > hl + 1) {
        // Right tree is taller; descend on its left spine.
        const JoinBuffer* jr = as_join_buffer(right.get());
        tptr<LStrObject> b(jr->left(), true);
        tptr<LStrObject> c(jr->right(), true);
        tptr<LStrObject> new_left = concat_balanced(type, left, b);
        if (!new_left) return {};
        tptr<LStrObject> node = make_join_lstr(type, new_left.ptr().get(), c.ptr().get());
        if (!node) return {};
        return rebalance_join(type, node);
    }

    tptr<LStrObject> node = make_join_lstr(type, left.ptr().get(), right.ptr().get());
    if (!node) return {};
    return rebalance_join(type, node);
}
