"""Tests for the lstring.L type: basic operations and behaviors.

All tests run with optimization disabled to preserve lazy buffer behavior.
"""

import unittest
import lstring


class TestLStr(unittest.TestCase):
    """Unit tests for the `L` type covering construction, concatenation,
    repetition, slicing, indexing and representation.

    Tests run with optimization disabled to keep lazy-buffer behavior
    deterministic.
    """
    @classmethod
    def setUpClass(cls):
        """Disable optimization for the test class."""
        cls.original_threshold = lstring.get_optimize_threshold()
        lstring.set_optimize_threshold(0)

    @classmethod
    def tearDownClass(cls):
        """Restore the original optimization threshold."""
        lstring.set_optimize_threshold(cls.original_threshold)

    def test_constructor_valid(self):
        """Constructing with a Python str produces the expected value."""
        s = lstring.L("hello")
        self.assertEqual(str(s), "hello")

    def test_constructor_invalid(self):
        """Passing a non-str to the constructor raises TypeError."""
        with self.assertRaises(TypeError):
            lstring.L(123)

    def test_concat_valid(self):
        """Concatenation of two L instances yields an L with expected contents."""
        s1 = lstring.L("foo")
        s2 = lstring.L("bar")
        s3 = s1 + s2
        self.assertIsInstance(s3, lstring.L)
        self.assertEqual(str(s3), "foobar")

    def test_concat_invalid(self):
        """Mixed concatenation with a Python str is supported by wrapping it.

        A Python `str` operand is wrapped into a temporary `L` and the
        result remains an `L` with expected value.
        """
        s = lstring.L("foo") + "bar"
        self.assertIsInstance(s, lstring.L)
        self.assertEqual(str(s), "foobar")

    def test_mul_valid(self):
        """Multiplication (repeat) tests."""
        s = lstring.L("ab")
        self.assertEqual(str(s * 3), "ababab")
        self.assertEqual(str(3 * s), "ababab")

    def test_mul_invalid_negative(self):
        """Multiplying by a negative integer raises RuntimeError."""
        with self.assertRaises(RuntimeError):
            _ = lstring.L("ab") * -1

    def test_mul_invalid_type(self):
        """Multiplying by a non-integer (e.g. float) raises TypeError."""
        with self.assertRaises(TypeError):
            _ = lstring.L("ab") * 2.5

    def test_slice_basic(self):
        """Slice-related tests."""
        s = lstring.L("012345")
        self.assertEqual(str(s[1:4]), "123")
        self.assertEqual(str(s[::2]), "024")
        self.assertEqual(str(s[::-1]), "543210")
        self.assertEqual(str(s[-4:-1]), "234")
        self.assertEqual(str(s[10:20]), "")

    def test_indexing(self):
        """Indexing tests (positive and negative indices)."""
        s = lstring.L("abc")
        self.assertEqual(s[1], "b")
        self.assertEqual(s[-1], "c")
        with self.assertRaises(IndexError):
            _ = s[10]

    def test_str_conversion(self):
        """Conversion to Python str via str()."""
        s = lstring.L("xyz")
        self.assertEqual(str(s), "xyz")

    def test_repr_contains_value(self):
        """Representation includes the contained value."""
        s = lstring.L("abc")
        r = repr(s)
        self.assertIn("abc", r)


if __name__ == "__main__":
    unittest.main()
