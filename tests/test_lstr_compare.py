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


class TestLStrMixedComparisons(unittest.TestCase):
    """Tests for comparisons between L and str."""
    
    def test_equality_with_str(self):
        """L can be compared for equality with str."""
        self.assertTrue(lstring.L("abc") == "abc")
        self.assertTrue("abc" == lstring.L("abc"))
        self.assertFalse(lstring.L("abc") == "def")
        self.assertFalse("def" == lstring.L("abc"))
    
    def test_inequality_with_str(self):
        """L can be compared for inequality with str."""
        self.assertTrue(lstring.L("abc") != "def")
        self.assertTrue("def" != lstring.L("abc"))
        self.assertFalse(lstring.L("abc") != "abc")
        self.assertFalse("abc" != lstring.L("abc"))
    
    def test_less_than_with_str(self):
        """L can be compared with < operator against str."""
        self.assertTrue(lstring.L("a") < "b")
        self.assertTrue("a" < lstring.L("b"))
        self.assertFalse(lstring.L("b") < "a")
        self.assertFalse("b" < lstring.L("a"))
        
        # Prefix comparisons
        self.assertTrue(lstring.L("ab") < "abc")
        self.assertTrue("ab" < lstring.L("abc"))
    
    def test_less_equal_with_str(self):
        """L can be compared with <= operator against str."""
        self.assertTrue(lstring.L("abc") <= "abc")
        self.assertTrue("abc" <= lstring.L("abc"))
        self.assertTrue(lstring.L("a") <= "b")
        self.assertTrue("a" <= lstring.L("b"))
        self.assertFalse(lstring.L("b") <= "a")
        self.assertFalse("b" <= lstring.L("a"))
    
    def test_greater_than_with_str(self):
        """L can be compared with > operator against str."""
        self.assertTrue(lstring.L("b") > "a")
        self.assertTrue("b" > lstring.L("a"))
        self.assertFalse(lstring.L("a") > "b")
        self.assertFalse("a" > lstring.L("b"))
        
        # Prefix comparisons
        self.assertTrue(lstring.L("abc") > "ab")
        self.assertTrue("abc" > lstring.L("ab"))
    
    def test_greater_equal_with_str(self):
        """L can be compared with >= operator against str."""
        self.assertTrue(lstring.L("abc") >= "abc")
        self.assertTrue("abc" >= lstring.L("abc"))
        self.assertTrue(lstring.L("b") >= "a")
        self.assertTrue("b" >= lstring.L("a"))
        self.assertFalse(lstring.L("a") >= "b")
        self.assertFalse("a" >= lstring.L("b"))


class TestLStrSubclassComparisons(unittest.TestCase):
    """Tests for comparisons between L subclasses."""
    
    def setUp(self):
        class SubL1(lstring.L):
            pass
        
        class SubL2(lstring.L):
            pass
        
        self.SubL1 = SubL1
        self.SubL2 = SubL2
    
    def test_subclass_equality(self):
        """Subclasses of L can be compared with each other."""
        a = self.SubL1("abc")
        b = self.SubL2("abc")
        c = self.SubL1("def")
        
        self.assertTrue(a == b)
        self.assertFalse(a == c)
    
    def test_subclass_ordering(self):
        """Subclasses of L support ordering comparisons."""
        a = self.SubL1("a")
        b = self.SubL2("b")
        
        self.assertTrue(a < b)
        self.assertTrue(b > a)
        self.assertTrue(a <= b)
        self.assertTrue(b >= a)
    
    def test_subclass_with_base(self):
        """Subclass can be compared with base L class."""
        a = self.SubL1("abc")
        b = lstring.L("abc")
        
        self.assertTrue(a == b)
        self.assertTrue(b == a)
    
    def test_subclass_with_str(self):
        """Subclass can be compared with str."""
        a = self.SubL1("abc")
        
        self.assertTrue(a == "abc")
        self.assertTrue("abc" == a)
        self.assertTrue(a < "b")
        self.assertTrue("b" > a)


if __name__ == "__main__":
    unittest.main()

