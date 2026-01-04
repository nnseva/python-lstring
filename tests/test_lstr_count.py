"""
Tests for count() method.
"""
import unittest
from lstring import L
import lstring


class TestCount(unittest.TestCase):
    """Tests for count() method."""
    
    @classmethod
    def setUpClass(cls):
        cls._orig_thresh = lstring.get_optimize_threshold()
        # disable C-level automatic collapsing/optimization for deterministic behavior
        lstring.set_optimize_threshold(0)

    @classmethod
    def tearDownClass(cls):
        lstring.set_optimize_threshold(cls._orig_thresh)
    
    def test_basic_count(self):
        """Basic count with multiple occurrences."""
        self.assertEqual(L("hello hello").count("hello"), 2)
        self.assertEqual(L("hello hello").count("l"), 4)
        self.assertEqual(L("hello").count("l"), 2)
    
    def test_count_zero(self):
        """Count returns 0 when substring not found."""
        self.assertEqual(L("hello").count("goodbye"), 0)
        self.assertEqual(L("abc").count("x"), 0)
    
    def test_count_empty_substring(self):
        """Empty substring appears at every position."""
        self.assertEqual(L("hello").count(""), 6)  # 5 chars + 1
        self.assertEqual(L("").count(""), 1)
        self.assertEqual(L("abc").count(""), 4)
    
    def test_count_non_overlapping(self):
        """Count should not count overlapping occurrences."""
        # "aa" appears 2 times non-overlapping in "aaaa"
        self.assertEqual(L("aaaa").count("aa"), 2)
        # "aaa" appears 1 time non-overlapping in "aaaa"
        self.assertEqual(L("aaaa").count("aaa"), 1)
        # "aba" appears 1 time non-overlapping in "ababa"
        self.assertEqual(L("ababa").count("aba"), 1)
    
    def test_count_single_char(self):
        """Count single character."""
        self.assertEqual(L("hello world").count("o"), 2)
        self.assertEqual(L("hello world").count("l"), 3)
        self.assertEqual(L("aaaaaa").count("a"), 6)
    
    def test_count_whole_string(self):
        """Count whole string as substring."""
        self.assertEqual(L("hello").count("hello"), 1)
        self.assertEqual(L("test").count("test"), 1)
    
    def test_count_longer_than_string(self):
        """Substring longer than string."""
        self.assertEqual(L("hi").count("hello"), 0)
    
    def test_count_with_start(self):
        """Count with start parameter."""
        s = L("hello hello hello")
        self.assertEqual(s.count("hello"), 3)
        self.assertEqual(s.count("hello", 6), 2)
        self.assertEqual(s.count("hello", 12), 1)
        self.assertEqual(s.count("l", 7), 4)
    
    def test_count_with_start_and_end(self):
        """Count with both start and end parameters."""
        s = L("hello hello hello")
        self.assertEqual(s.count("hello", 0, 11), 2)
        self.assertEqual(s.count("hello", 0, 5), 1)
        self.assertEqual(s.count("l", 2, 9), 3)
        self.assertEqual(s.count("hello", 6, 11), 1)
    
    def test_count_negative_start(self):
        """Count with negative start index."""
        s = L("hello hello")
        self.assertEqual(s.count("hello", -5), 1)
        self.assertEqual(s.count("l", -7), 2)
    
    def test_count_negative_end(self):
        """Count with negative end index."""
        s = L("hello hello")
        self.assertEqual(s.count("hello", 0, -6), 1)
        self.assertEqual(s.count("l", 0, -7), 2)
    
    def test_count_out_of_range_indices(self):
        """Count with out of range indices."""
        s = L("hello")
        self.assertEqual(s.count("hello", -100, 100), 1)
        self.assertEqual(s.count("l", 100), 0)
        self.assertEqual(s.count("l", 0, 0), 0)
    
    def test_count_with_L_instance(self):
        """Count with L instance as substring."""
        self.assertEqual(L("hello hello").count(L("hello")), 2)
        self.assertEqual(L("test test").count(L("t")), 4)
    
    def test_comparison_with_str(self):
        """Compare behavior with Python str."""
        test_cases = [
            ("hello hello", "hello", None, None),
            ("hello hello", "l", None, None),
            ("aaaa", "aa", None, None),
            ("hello hello hello", "hello", 6, None),
            ("hello hello", "hello", 0, 5),
            ("test", "", None, None),
            ("", "", None, None),
            ("ababa", "aba", None, None),
        ]
        for s, sub, start, end in test_cases:
            ls = L(s)
            if start is None and end is None:
                self.assertEqual(ls.count(sub), s.count(sub),
                               f"Failed for count({repr(sub)})")
            elif end is None:
                self.assertEqual(ls.count(sub, start), s.count(sub, start),
                               f"Failed for count({repr(sub)}, {start})")
            else:
                self.assertEqual(ls.count(sub, start, end), s.count(sub, start, end),
                               f"Failed for count({repr(sub)}, {start}, {end})")
    
    def test_type_error(self):
        """Test that invalid types raise TypeError."""
        with self.assertRaises(TypeError):
            L("hello").count(123)
        with self.assertRaises(TypeError):
            L("hello").count(None)


class TestCountBufferTypes(unittest.TestCase):
    """Test count works correctly with different buffer types."""
    
    def test_slice_buffer(self):
        """Test with SliceBuffer."""
        s = L("xxxhello hello helloxxx")[3:-3]
        self.assertEqual(s.count("hello"), 3)
        self.assertEqual(s.count("l"), 6)
        self.assertEqual(s.count("xxx"), 0)
    
    def test_join_buffer(self):
        """Test with JoinBuffer."""
        s = L("hello") + L(" ") + L("hello")
        self.assertEqual(s.count("hello"), 2)
        self.assertEqual(s.count(" "), 1)
        self.assertEqual(s.count("l"), 4)
    
    def test_mul_buffer(self):
        """Test with MulBuffer."""
        s = L("abc") * 3
        self.assertEqual(s.count("abc"), 3)
        self.assertEqual(s.count("a"), 3)
        self.assertEqual(s.count("ca"), 2)


class TestCountEdgeCases(unittest.TestCase):
    """Edge case tests for count."""
    
    def test_count_at_boundaries(self):
        """Test occurrences at string boundaries."""
        s = L("hello")
        self.assertEqual(s.count("h"), 1)  # at start
        self.assertEqual(s.count("o"), 1)  # at end
        self.assertEqual(s.count("hello"), 1)  # whole string
    
    def test_count_repeated_pattern(self):
        """Test with repeated patterns."""
        self.assertEqual(L("ababab").count("ab"), 3)
        self.assertEqual(L("aaaa").count("a"), 4)
        self.assertEqual(L("121212").count("12"), 3)
    
    def test_count_overlapping_pattern(self):
        """Verify overlapping patterns are not counted."""
        # "aaa" in "aaaaa" - only 1 non-overlapping occurrence
        self.assertEqual(L("aaaaa").count("aaa"), 1)
        # "aba" in "ababa" - only 1 non-overlapping occurrence
        self.assertEqual(L("ababa").count("aba"), 1)
    
    def test_count_unicode(self):
        """Test with Unicode strings."""
        self.assertEqual(L("Привет мир Привет").count("Привет"), 2)
        self.assertEqual(L("こんにちは世界").count("こ"), 1)
    
    def test_count_empty_string(self):
        """Count on empty string."""
        self.assertEqual(L("").count("a"), 0)
        self.assertEqual(L("").count(""), 1)
    
    def test_count_consecutive_matches(self):
        """Test consecutive matches."""
        # Each "aa" is counted once in "aaaa"
        self.assertEqual(L("aaaa").count("aa"), 2)
        # Each "11" is counted once in "111111"
        self.assertEqual(L("111111").count("11"), 3)


if __name__ == '__main__':
    unittest.main()
