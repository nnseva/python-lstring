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


class TestBufferTypeComparisons(unittest.TestCase):
    """Tests for comparisons between different buffer types."""
    
    def test_strbuffer_vs_strbuffer(self):
        """StrBuffer vs StrBuffer uses optimized PyUnicode_Compare."""
        a = lstring.L("abc")
        b = lstring.L("abc")
        c = lstring.L("abd")
        
        # Both are StrBuffer internally
        self.assertTrue(a == b)
        self.assertTrue(a < c)
        self.assertTrue(c > a)
    
    def test_joinbuffer_vs_strbuffer(self):
        """JoinBuffer vs StrBuffer comparison."""
        # JoinBuffer (concatenation)
        a = lstring.L("ab") + lstring.L("c")
        # StrBuffer
        b = lstring.L("abc")
        c = lstring.L("abd")
        
        self.assertTrue(a == b)
        self.assertTrue(a < c)
        self.assertTrue(c > a)
    
    def test_mulbuffer_vs_strbuffer(self):
        """MulBuffer vs StrBuffer comparison."""
        # MulBuffer (repetition)
        a = lstring.L("ab") * 2
        # StrBuffer
        b = lstring.L("abab")
        c = lstring.L("abac")
        
        self.assertTrue(a == b)
        self.assertTrue(a < c)
        self.assertTrue(c > a)
    
    def test_slicebuffer_vs_strbuffer(self):
        """SliceBuffer vs StrBuffer comparison."""
        # Slice1Buffer (step == 1)
        a = lstring.L("abcdef")[1:4]
        # StrBuffer
        b = lstring.L("bcd")
        c = lstring.L("bce")
        
        self.assertTrue(a == b)
        self.assertTrue(a < c)
        self.assertTrue(c > a)
    
    def test_slicebuffer_step_vs_strbuffer(self):
        """SliceBuffer with step vs StrBuffer comparison."""
        # SliceBuffer (step != 1)
        a = lstring.L("abcdef")[::2]  # "ace"
        # StrBuffer
        b = lstring.L("ace")
        c = lstring.L("acf")
        
        self.assertTrue(a == b)
        self.assertTrue(a < c)
        self.assertTrue(c > a)
    
    def test_joinbuffer_vs_joinbuffer(self):
        """JoinBuffer vs JoinBuffer comparison."""
        a = lstring.L("ab") + lstring.L("c")
        b = lstring.L("a") + lstring.L("bc")
        c = lstring.L("ab") + lstring.L("d")
        
        self.assertTrue(a == b)
        self.assertTrue(a < c)
        self.assertTrue(c > a)
    
    def test_mulbuffer_vs_mulbuffer(self):
        """MulBuffer vs MulBuffer comparison."""
        a = lstring.L("ab") * 3
        b = lstring.L("a") * 6  # "aaaaaa"
        c = lstring.L("ab") * 2  # "abab"
        
        # "ababab" vs "aaaaaa" - first diff at position 1
        self.assertTrue(a > b)
        self.assertTrue(b < a)
        # "ababab" vs "abab" - length differs
        self.assertTrue(a > c)
        self.assertTrue(c < a)
    
    def test_slicebuffer_vs_slicebuffer(self):
        """SliceBuffer vs SliceBuffer comparison."""
        src = lstring.L("abcdefgh")
        a = src[1:5]  # "bcde"
        b = src[2:6]  # "cdef"
        c = src[1:5]  # "bcde"
        
        self.assertTrue(a == c)
        self.assertTrue(a < b)
        self.assertTrue(b > a)
    
    def test_complex_joinbuffer_comparison(self):
        """Complex nested JoinBuffer comparison."""
        # Nested concatenations
        a = lstring.L("a") + lstring.L("b") + lstring.L("c")
        b = (lstring.L("ab") + lstring.L("c"))
        c = lstring.L("abc")
        
        self.assertTrue(a == b)
        self.assertTrue(a == c)
        self.assertTrue(b == c)
    
    def test_mixed_buffer_types(self):
        """Comparison between multiple different buffer types."""
        # StrBuffer
        str_buf = lstring.L("abab")
        # JoinBuffer
        join_buf = lstring.L("ab") + lstring.L("ab")
        # MulBuffer
        mul_buf = lstring.L("ab") * 2
        # SliceBuffer
        slice_buf = lstring.L("xababx")[1:5]
        
        # All should be equal
        self.assertTrue(str_buf == join_buf)
        self.assertTrue(str_buf == mul_buf)
        self.assertTrue(str_buf == slice_buf)
        self.assertTrue(join_buf == mul_buf)
        self.assertTrue(join_buf == slice_buf)
        self.assertTrue(mul_buf == slice_buf)
    
    def test_empty_buffer_comparisons(self):
        """Comparison with empty buffers of different types."""
        # StrBuffer
        empty_str = lstring.L("")
        # JoinBuffer (empty concatenation)
        empty_join = lstring.L("") + lstring.L("")
        # SliceBuffer (empty slice)
        empty_slice = lstring.L("abc")[0:0]
        
        # All empty buffers should be equal
        self.assertTrue(empty_str == empty_join)
        self.assertTrue(empty_str == empty_slice)
        self.assertTrue(empty_join == empty_slice)
        
        # Empty < non-empty
        non_empty = lstring.L("a")
        self.assertTrue(empty_str < non_empty)
        self.assertTrue(empty_join < non_empty)
        self.assertTrue(empty_slice < non_empty)
    
    def test_unicode_different_widths(self):
        """Comparison with different Unicode character widths."""
        # ASCII (1-byte)
        ascii_buf = lstring.L("abc")
        # Cyrillic (2-byte)
        cyrillic_buf = lstring.L("абв")
        # Emoji (4-byte)
        emoji_buf = lstring.L("😀😁😂")
        
        # Each should compare equal to itself
        self.assertTrue(ascii_buf == lstring.L("abc"))
        self.assertTrue(cyrillic_buf == lstring.L("абв"))
        self.assertTrue(emoji_buf == lstring.L("😀😁😂"))
        
        # Different content should not be equal
        self.assertFalse(ascii_buf == cyrillic_buf)
        self.assertFalse(ascii_buf == emoji_buf)
        self.assertFalse(cyrillic_buf == emoji_buf)
    
    def test_mixed_operations_comparison(self):
        """Comparison of results from mixed operations."""
        # (slice + concat) * repeat
        a = (lstring.L("hello")[1:4] + lstring.L("x")) * 2  # "ellxellx"
        b = lstring.L("ellx") * 2
        c = lstring.L("ellxellx")
        
        self.assertTrue(a == b)
        self.assertTrue(a == c)
        self.assertTrue(b == c)
        
        # Different result
        d = lstring.L("ellxell")
        self.assertTrue(a > d)  # "ellxellx" > "ellxell"
        self.assertTrue(d < a)


if __name__ == "__main__":
    unittest.main()

