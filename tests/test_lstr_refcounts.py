"""Reference-counting tests for lstring._lstr operations.

Utilities:
 - dyn(s): create a dynamic (non-interned) string equal to `s`.
"""

import unittest
import sys
import gc
import lstring


def dyn(s: str) -> str:
    """Create a dynamic (non-interned) string equal to `s`.

    Using join creates a new string object at runtime and avoids interned
    literal behavior.
    """
    return "".join(s)

class TestLStrRefCounts(unittest.TestCase):
    """Reference-counting tests covering _lstr operations.

    These tests verify that various lazy operations (construction, concat,
    repeat, slice, indexing, repr/str) do not leak or change refcounts of the
    original Python string objects used as sources. Garbage collection is
    controlled around tests to make refcount measurements deterministic.
    """
    @classmethod
    def setUpClass(cls):
        """Disable optimization for predictable lazy buffer behavior."""
        cls.original_threshold = lstring.get_optimize_threshold()
        lstring.set_optimize_threshold(0)

    @classmethod
    def tearDownClass(cls):
        """Restore the optimization threshold after the test class finishes."""
        lstring.set_optimize_threshold(cls.original_threshold)

    def setUp(self):
        """Collect garbage before each test to stabilize reference counts."""
        gc.collect()

    def tearDown(self):
        """Collect garbage after each test to clean up temporary objects."""
        gc.collect()

    def kinds(self):
        """Yield dynamic strings covering Unicode kinds: 1-byte, 2-byte (BMP), 4-byte (astral)."""
        yield dyn("abcd")                               # 1-byte (Latin-1)
        yield dyn("\u03B1\u03B2\u03B3")                 # 2-byte (Greek alpha/beta/gamma)
        yield dyn("\U0001F600\U0001F601")               # 4-byte (grinning face, beaming face)

    def pairs(self):
        """Yield pairs of dynamic strings mixing kinds (same and mixed)."""
        k = list(self.kinds())
        for i in range(len(k)):
            for j in range(len(k)):
                yield (k[i], k[j])
    def test_constructor_refcounts(self):
        """Constructing and deleting an `_lstr` does not change the source refcount."""
        for s in self.kinds():
            with self.subTest(src=s):
                before = sys.getrefcount(s)
                x = lstring._lstr(s)
                tmp = str(x)  # make sure object is used
                del tmp
                del x
                gc.collect()
                after = sys.getrefcount(s)
                self.assertEqual(after, before)

    def test_concat_refcounts(self):
        """Concatenating two `_lstr` instances does not affect original strings' refcounts."""
        for a, b in self.pairs():
            with self.subTest(left=a, right=b):
                before_a = sys.getrefcount(a)
                before_b = sys.getrefcount(b)

                x = lstring._lstr(a)
                y = lstring._lstr(b)
                z = x + y
                tmp = str(z)
                del tmp
                del z, x, y
                gc.collect()

                after_a = sys.getrefcount(a)
                after_b = sys.getrefcount(b)
                self.assertEqual(after_a, before_a)
                self.assertEqual(after_b, before_b)

    def test_concat_lstr_plus_str_refcounts(self):
        """Mixing `_lstr + str` preserves refcounts of both operands."""
        for a in self.kinds():
            for b in self.kinds():
                with self.subTest(left=a, right=b):
                    before_a = sys.getrefcount(a)
                    before_b = sys.getrefcount(b)

                    x = lstring._lstr(a)
                    z = x + b
                    tmp = str(z)
                    del tmp
                    del z, x
                    gc.collect()

                    after_a = sys.getrefcount(a)
                    after_b = sys.getrefcount(b)
                    self.assertEqual(after_a, before_a)
                    self.assertEqual(after_b, before_b)

    def test_concat_str_plus_lstr_refcounts(self):
        """Mixing `str + _lstr` preserves refcounts of both operands."""
        for a in self.kinds():
            for b in self.kinds():
                with self.subTest(left=a, right=b):
                    before_a = sys.getrefcount(a)
                    before_b = sys.getrefcount(b)

                    y = lstring._lstr(b)
                    z = a + y
                    tmp = str(z)
                    del tmp
                    del z, y
                    gc.collect()

                    after_a = sys.getrefcount(a)
                    after_b = sys.getrefcount(b)
                    self.assertEqual(after_a, before_a)
                    self.assertEqual(after_b, before_b)

    def test_concat_invalid_arg_refcounts(self):
        """Concatenation with incompatible operand raises TypeError without changing refcounts."""
        for s in self.kinds():
            with self.subTest(src=s):
                # create a dynamic non-lstr object (distinct type each loop)
                bad = type("Bad", (), {})()
                # check left: _lstr + bad
                before_l = sys.getrefcount(s)
                before_b = sys.getrefcount(bad)
                x = lstring._lstr(s)
                try:
                    with self.assertRaises(TypeError):
                        _ = x + bad
                finally:
                    del x
                    gc.collect()
                after_l = sys.getrefcount(s)
                after_b = sys.getrefcount(bad)
                self.assertEqual(after_l, before_l)
                self.assertEqual(after_b, before_b)

                # check right: bad + _lstr
                bad2 = type("Bad2", (), {})()
                before_l2 = sys.getrefcount(s)
                before_b2 = sys.getrefcount(bad2)
                y = lstring._lstr(s)
                try:
                    with self.assertRaises(TypeError):
                        _ = bad2 + y
                finally:
                    del y
                    gc.collect()
                after_l2 = sys.getrefcount(s)
                after_b2 = sys.getrefcount(bad2)
                self.assertEqual(after_l2, before_l2)
                self.assertEqual(after_b2, before_b2)

    def test_mul_refcounts(self):
        """Repeating an `_lstr` leaves the source string's refcount unchanged."""
        for s in self.kinds():
            with self.subTest(src=s):
                before = sys.getrefcount(s)
                x = lstring._lstr(s)

                r1 = x * 3
                r2 = 2 * x
                tmp = (str(r1), str(r2))
                del tmp

                del r1, r2, x
                gc.collect()
                after = sys.getrefcount(s)
                self.assertEqual(after, before)

    def test_slice_refcounts(self):
        """Different slicing patterns must not change the source string's refcount."""
        for s in self.kinds():
            with self.subTest(src=s):
                before = sys.getrefcount(s)
                x = lstring._lstr(s)

                subs = [
                    x[1:4],
                    x[::2],
                    x[::-1],
                    x[-4:-1],
                    x[10:20],
                ]
                tmp = [str(u) for u in subs]
                del tmp

                del subs, x
                gc.collect()
                after = sys.getrefcount(s)
                self.assertEqual(after, before)

    def test_index_refcounts(self):
        """Indexing a string (positive/negative) must not affect the source refcount."""
        for s in self.kinds():
            with self.subTest(src=s):
                before = sys.getrefcount(s)
                x = lstring._lstr(s)

                if len(s) >= 2:
                    ch1 = x[1]
                    del ch1
                ch_last = x[-1]
                del ch_last

                del x
                gc.collect()
                after = sys.getrefcount(s)
                self.assertEqual(after, before)

    def test_str_conversion_refcounts(self):
        """Converting an `_lstr` to str does not change the source string's refcount."""
        for s in self.kinds():
            with self.subTest(src=s):
                before = sys.getrefcount(s)
                x = lstring._lstr(s)
                tmp = str(x)
                del tmp
                del x
                gc.collect()
                after = sys.getrefcount(s)
                self.assertEqual(after, before)

    def test_repr_refcounts(self):
        """Calling repr() on an `_lstr` must not affect the source string's refcount."""
        for s in self.kinds():
            with self.subTest(src=s):
                before = sys.getrefcount(s)
                x = lstring._lstr(s)
                r = repr(x)
                del r, x
                gc.collect()
                after = sys.getrefcount(s)
                self.assertEqual(after, before)

    def test_error_mul_float_refcounts(self):
        """Multiplying by a float raises TypeError and preserves source refcount."""
        for s in self.kinds():
            with self.subTest(src=s):
                before = sys.getrefcount(s)
                x = lstring._lstr(s)
                with self.assertRaises(TypeError):
                    _ = x * 2.5
                del x
                gc.collect()
                after = sys.getrefcount(s)
                self.assertEqual(after, before)

    def test_error_mul_negative_refcounts(self):
        """Multiplying by a negative integer raises RuntimeError and preserves refcount."""
        for s in self.kinds():
            with self.subTest(src=s):
                before = sys.getrefcount(s)
                x = lstring._lstr(s)
                with self.assertRaises(RuntimeError):
                    _ = x * -1
                del x
                gc.collect()
                after = sys.getrefcount(s)
                self.assertEqual(after, before)

    def test_error_index_out_of_range_refcounts(self):
        """Indexing out of range raises IndexError and preserves source refcount."""
        for s in self.kinds():
            with self.subTest(src=s):
                before = sys.getrefcount(s)
                x = lstring._lstr(s)
                with self.assertRaises(IndexError):
                    _ = x[len(s) + 5]
                del x
                gc.collect()
                after = sys.getrefcount(s)
                self.assertEqual(after, before)

    def test_error_slice_zero_step_refcounts(self):
        """Slicing with a zero step raises ValueError and does not affect refcounts."""
        for s in self.kinds():
            with self.subTest(src=s):
                before = sys.getrefcount(s)
                x = lstring._lstr(s)
                with self.assertRaises(ValueError):
                    _ = x[::0]
                del x
                gc.collect()
                after = sys.getrefcount(s)
                self.assertEqual(after, before)

    def test_mixed_chain_refcounts(self):
        """Stress multiple mixed-kind operations and assert no leakage of source refcounts."""
        a = dyn("abcd")                             # 1-byte
        b = dyn("\u03B1\u03B2\u03B3")               # 2-byte
        c = dyn("\U0001F600\U0001F601")             # 4-byte

        before_a = sys.getrefcount(a)
        before_b = sys.getrefcount(b)
        before_c = sys.getrefcount(c)

        x = lstring._lstr(a)
        y = lstring._lstr(b)
        z = lstring._lstr(c)

        before_x = sys.getrefcount(x)
        before_y = sys.getrefcount(y)
        before_z = sys.getrefcount(z)

        self.assertEqual(sys.getrefcount(a), before_a + 1)
        self.assertEqual(sys.getrefcount(b), before_b + 1)
        self.assertEqual(sys.getrefcount(c), before_c + 1)

        w1 = x + y
        w2 = y + z
        w3 = z + x

        before_w1 = sys.getrefcount(w1)
        before_w2 = sys.getrefcount(w2)
        before_w3 = sys.getrefcount(w3)

        self.assertEqual(sys.getrefcount(x), before_x + 2)
        self.assertEqual(sys.getrefcount(y), before_y + 2)
        self.assertEqual(sys.getrefcount(z), before_z + 2)

        self.assertEqual(sys.getrefcount(a), before_a + 1)
        self.assertEqual(sys.getrefcount(b), before_b + 1)
        self.assertEqual(sys.getrefcount(c), before_c + 1)

        p1 = w1 * 2
        p2 = 3 * w2

        before_p1 = sys.getrefcount(p1)
        before_p2 = sys.getrefcount(p2)

        self.assertEqual(sys.getrefcount(w1), before_w1 + 1)
        self.assertEqual(sys.getrefcount(w2), before_w2 + 1)
        self.assertEqual(sys.getrefcount(w3), before_w3)

        self.assertEqual(sys.getrefcount(a), before_a + 1)
        self.assertEqual(sys.getrefcount(b), before_b + 1)
        self.assertEqual(sys.getrefcount(c), before_c + 1)

        s1 = w3[1:5]
        s2 = w2[::-1]
        s3 = w1[::2]

        before_s1 = sys.getrefcount(s1)
        before_s2 = sys.getrefcount(s2)
        before_s3 = sys.getrefcount(s3)

        self.assertEqual(sys.getrefcount(w1), before_w1 + 2)
        self.assertEqual(sys.getrefcount(w2), before_w2 + 2)
        self.assertEqual(sys.getrefcount(w3), before_w3 + 1)

        i1 = x[-1]
        i2 = y[1]

        self.assertEqual(sys.getrefcount(x), before_x + 2)
        self.assertEqual(sys.getrefcount(y), before_y + 2)

        s_all = [str(t) for t in (w1, w2, w3, x, y, z)]

        self.assertEqual(sys.getrefcount(w1), before_w1 + 2)
        self.assertEqual(sys.getrefcount(w2), before_w2 + 2)
        self.assertEqual(sys.getrefcount(w3), before_w3 + 1)

        self.assertEqual(sys.getrefcount(x), before_x + 2)
        self.assertEqual(sys.getrefcount(y), before_y + 2)
        self.assertEqual(sys.getrefcount(z), before_z + 2)

        them_all = (p1, p2, s1, s2, s3, i1, i2, s_all)
        del them_all

        self.assertEqual(sys.getrefcount(p1), before_p1)
        self.assertEqual(sys.getrefcount(p2), before_p2)

        self.assertEqual(sys.getrefcount(s1), before_s1)
        self.assertEqual(sys.getrefcount(s2), before_s2)
        self.assertEqual(sys.getrefcount(s3), before_s3)

        del w1, w2, w3, p1, p2, s1, s2, s3, i1, i2, s_all
        del x, y, z
        gc.collect()

        after_a = sys.getrefcount(a)
        after_b = sys.getrefcount(b)
        after_c = sys.getrefcount(c)

        self.assertEqual(after_a, before_a)
        self.assertEqual(after_b, before_b)
        self.assertEqual(after_c, before_c)


if __name__ == "__main__":
    unittest.main()
