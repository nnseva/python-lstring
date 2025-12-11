import unittest
import sys
import gc
import lstring

def dyn(s: str) -> str:
    """Create a dynamic (non-interned) string equal to `s`."""
    # Using join creates a new string object at runtime and avoids interned literal behavior.
    return "".join(s)

class TestLStrRefCounts(unittest.TestCase):
    def setUp(self):
        gc.collect()

    def tearDown(self):
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

    # --- Constructor ---
    def test_constructor_refcounts(self):
        # Constructing and deleting _lstr must not change source string's refcount.
        for s in self.kinds():
            with self.subTest(src=s):
                before = sys.getrefcount(s)
                x = lstring._lstr(s)
                tmp = str(x)  # make sure object is used
                del tmp
                del x
                gc.collect()
                after = sys.getrefcount(s)
                # Compare directly in test body to avoid extra references.
                self.assertEqual(after, before)

    # --- Concatenation ---
    def test_concat_refcounts(self):
        # Concatenation across all pairs (including mixed kinds) must keep sources' refcounts unchanged.
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

    # --- Multiplication (_lstr * int and int * _lstr) ---
    def test_mul_refcounts(self):
        # Multiplication must not affect source string's refcount.
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

    # --- Slicing ---
    def test_slice_refcounts(self):
        # Slicing patterns must not affect source string's refcount.
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

    # --- Indexing ---
    def test_index_refcounts(self):
        # Indexing (positive and negative) must leave source refcount unchanged.
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

    # --- str conversion ---
    def test_str_conversion_refcounts(self):
        # str(_lstr) must not change source string's refcount.
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

    # --- Repr ---
    def test_repr_refcounts(self):
        # repr(_lstr) must not change the source string's refcount.
        for s in self.kinds():
            with self.subTest(src=s):
                before = sys.getrefcount(s)
                x = lstring._lstr(s)
                r = repr(x)
                del r, x
                gc.collect()
                after = sys.getrefcount(s)
                self.assertEqual(after, before)

    # --- Error cases ---
    def test_error_mul_float_refcounts(self):
        # Multiplication by float -> TypeError; source refcount must remain unchanged.
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
        # Multiplication by negative -> RuntimeError; source refcount must remain unchanged.
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
        # Index out of range -> IndexError; source refcount must remain unchanged.
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
        # Slice with step=0 -> ValueError; source refcount must remain unchanged.
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

    # --- Mixed-kind stress chain ---
    def test_mixed_chain_refcounts(self):
        # Stress multiple operations across mixed kinds; all source refcounts must remain unchanged.
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
