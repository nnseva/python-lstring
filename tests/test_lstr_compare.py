import unittest
import lstring

class TestLStrComparisons(unittest.TestCase):
    def setUp(self):
        self.a = lstring.lstr("abc")
        self.b = lstring.lstr("abc")
        self.c = lstring.lstr("abd")
        self.d = lstring.lstr("ab")
        self.e = lstring.lstr("abcd")

    def test_equality(self):
        # Equal strings
        self.assertTrue(self.a == self.b)
        self.assertFalse(self.a != self.b)

        # Different strings
        self.assertFalse(self.a == self.c)
        self.assertTrue(self.a != self.c)

    def test_less_than(self):
        # "abc" < "abd"
        self.assertTrue(self.a < self.c)
        self.assertFalse(self.c < self.a)

        # "ab" < "abc"
        self.assertTrue(self.d < self.a)
        self.assertFalse(self.a < self.d)

    def test_less_equal(self):
        self.assertTrue(self.a <= self.b)  # equal
        self.assertTrue(self.a <= self.c)  # less
        self.assertFalse(self.c <= self.a)

    def test_greater_than(self):
        self.assertTrue(self.c > self.a)
        self.assertFalse(self.a > self.c)

        self.assertTrue(self.a > self.d)
        self.assertFalse(self.d > self.a)

    def test_greater_equal(self):
        self.assertTrue(self.a >= self.b)  # equal
        self.assertTrue(self.c >= self.a)  # greater
        self.assertFalse(self.a >= self.c)

    def test_prefix_suffix(self):
        # "abc" < "abcd"
        self.assertTrue(self.a < self.e)
        self.assertFalse(self.e < self.a)
        self.assertTrue(self.e > self.a)

if __name__ == "__main__":
    unittest.main()
