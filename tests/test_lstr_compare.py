"""Comparison tests for lstring.L objects."""

import unittest
import lstring


class TestLStrComparisons(unittest.TestCase):
    """Tests for equality and ordering comparisons."""
    def setUp(self):
        self.a = lstring.L("abc")
        self.b = lstring.L("abc")
        self.c = lstring.L("abd")
        self.d = lstring.L("ab")
        self.e = lstring.L("abcd")

    def test_equality(self):
        """Equality and inequality for identical and different contents."""
        # Equal strings
        self.assertTrue(self.a == self.b)
        self.assertFalse(self.a != self.b)

        # Different strings
        self.assertFalse(self.a == self.c)
        self.assertTrue(self.a != self.c)

    def test_less_than(self):
        """Less-than ordering tests, including prefix comparisons."""
        # "abc" < "abd"
        self.assertTrue(self.a < self.c)
        self.assertFalse(self.c < self.a)

        # "ab" < "abc"
        self.assertTrue(self.d < self.a)
        self.assertFalse(self.a < self.d)

    def test_less_equal(self):
        """Less-than-or-equal comparisons for equal and non-equal values."""
        self.assertTrue(self.a <= self.b)  # equal
        self.assertTrue(self.a <= self.c)  # less
        self.assertFalse(self.c <= self.a)

    def test_greater_than(self):
        """Greater-than ordering tests, corresponding to less-than cases."""
        self.assertTrue(self.c > self.a)
        self.assertFalse(self.a > self.c)

        self.assertTrue(self.a > self.d)
        self.assertFalse(self.d > self.a)

    def test_greater_equal(self):
        """Greater-than-or-equal comparisons for equal and greater values."""
        self.assertTrue(self.a >= self.b)  # equal
        self.assertTrue(self.c >= self.a)  # greater
        self.assertFalse(self.a >= self.c)

    def test_prefix_suffix(self):
        """Ensure prefix/suffix ordering behaves as expected (shorter < longer if prefix)."""
        # "abc" < "abcd"
        self.assertTrue(self.a < self.e)
        self.assertFalse(self.e < self.a)
        self.assertTrue(self.e > self.a)

if __name__ == "__main__":
    unittest.main()
