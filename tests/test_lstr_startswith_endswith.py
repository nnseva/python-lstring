"""
Tests for startswith() and endswith() methods.
"""
import unittest
from lstring import L
import lstring


class TestStartsWith(unittest.TestCase):
    """Tests for startswith() method."""
    
    @classmethod
    def setUpClass(cls):
        cls._orig_thresh = lstring.get_optimize_threshold()
        # disable C-level automatic collapsing/optimization for deterministic behavior
        lstring.set_optimize_threshold(0)

    @classmethod
    def tearDownClass(cls):
        lstring.set_optimize_threshold(cls._orig_thresh)
    
    def test_basic_startswith_true(self):
        """Basic startswith with matching prefix."""
        self.assertTrue(L("hello world").startswith("hello"))
        self.assertTrue(L("hello world").startswith(L("hello")))
    
    def test_basic_startswith_false(self):
        """Basic startswith with non-matching prefix."""
        self.assertFalse(L("hello world").startswith("world"))
        self.assertFalse(L("hello world").startswith("goodbye"))
    
    def test_empty_prefix(self):
        """Empty prefix should always return True."""
        self.assertTrue(L("hello").startswith(""))
        self.assertTrue(L("").startswith(""))
    
    def test_prefix_longer_than_string(self):
        """Prefix longer than string should return False."""
        self.assertFalse(L("hi").startswith("hello"))
    
    def test_exact_match(self):
        """Prefix equals entire string."""
        self.assertTrue(L("hello").startswith("hello"))
    
    def test_with_start_parameter(self):
        """Test with start parameter."""
        s = L("hello world")
        self.assertTrue(s.startswith("world", 6))
        self.assertTrue(s.startswith("lo", 3))
        self.assertFalse(s.startswith("hello", 1))
    
    def test_with_start_and_end_parameters(self):
        """Test with both start and end parameters."""
        s = L("hello world")
        self.assertTrue(s.startswith("hello", 0, 5))
        self.assertTrue(s.startswith("lo", 3, 8))
        self.assertFalse(s.startswith("world", 0, 5))
    
    def test_negative_start(self):
        """Test with negative start index."""
        s = L("hello world")
        self.assertTrue(s.startswith("world", -5))
        self.assertTrue(s.startswith("o w", -7))
    
    def test_negative_end(self):
        """Test with negative end index."""
        s = L("hello world")
        self.assertTrue(s.startswith("hello", 0, -6))
        self.assertFalse(s.startswith("hello", 0, -7))
    
    def test_out_of_range_indices(self):
        """Test with out of range indices."""
        s = L("hello")
        self.assertTrue(s.startswith("hello", -100, 100))
        self.assertFalse(s.startswith("x", 100))
    
    def test_comparison_with_str(self):
        """Compare behavior with Python str."""
        test_cases = [
            ("hello world", "hello", None, None),
            ("hello world", "world", 6, None),
            ("hello world", "lo", 3, 8),
            ("hello world", "", None, None),
            ("hello", "hello world", None, None),
            ("test", "st", -2, None),
        ]
        for s, prefix, start, end in test_cases:
            ls = L(s)
            if start is None and end is None:
                self.assertEqual(ls.startswith(prefix), s.startswith(prefix),
                               f"Failed for startswith({repr(prefix)})")
            elif end is None:
                self.assertEqual(ls.startswith(prefix, start), s.startswith(prefix, start),
                               f"Failed for startswith({repr(prefix)}, {start})")
            else:
                self.assertEqual(ls.startswith(prefix, start, end), s.startswith(prefix, start, end),
                               f"Failed for startswith({repr(prefix)}, {start}, {end})")
    
    def test_type_error(self):
        """Test that invalid types raise TypeError."""
        with self.assertRaises(TypeError):
            L("hello").startswith(123)
        with self.assertRaises(TypeError):
            L("hello").startswith(None)


class TestEndsWith(unittest.TestCase):
    """Tests for endswith() method."""
    
    def test_basic_endswith_true(self):
        """Basic endswith with matching suffix."""
        self.assertTrue(L("hello world").endswith("world"))
        self.assertTrue(L("hello world").endswith(L("world")))
    
    def test_basic_endswith_false(self):
        """Basic endswith with non-matching suffix."""
        self.assertFalse(L("hello world").endswith("hello"))
        self.assertFalse(L("hello world").endswith("goodbye"))
    
    def test_empty_suffix(self):
        """Empty suffix should always return True."""
        self.assertTrue(L("hello").endswith(""))
        self.assertTrue(L("").endswith(""))
    
    def test_suffix_longer_than_string(self):
        """Suffix longer than string should return False."""
        self.assertFalse(L("hi").endswith("hello"))
    
    def test_exact_match(self):
        """Suffix equals entire string."""
        self.assertTrue(L("hello").endswith("hello"))
    
    def test_with_start_parameter(self):
        """Test with start parameter."""
        s = L("hello world")
        self.assertTrue(s.endswith("world", 6))
        self.assertFalse(s.endswith("world", 7))
    
    def test_with_start_and_end_parameters(self):
        """Test with both start and end parameters."""
        s = L("hello world")
        self.assertTrue(s.endswith("hello", 0, 5))
        self.assertTrue(s.endswith("lo", 0, 5))
        self.assertFalse(s.endswith("world", 0, 5))
    
    def test_negative_start(self):
        """Test with negative start index."""
        s = L("hello world")
        self.assertTrue(s.endswith("world", -5))
        self.assertTrue(s.endswith("rld", -3))
    
    def test_negative_end(self):
        """Test with negative end index."""
        s = L("hello world")
        self.assertTrue(s.endswith("hello", 0, -6))
        self.assertFalse(s.endswith("hello", 0, -7))
    
    def test_out_of_range_indices(self):
        """Test with out of range indices."""
        s = L("hello")
        self.assertTrue(s.endswith("hello", -100, 100))
        self.assertFalse(s.endswith("x", 0, 0))
    
    def test_comparison_with_str(self):
        """Compare behavior with Python str."""
        test_cases = [
            ("hello world", "world", None, None),
            ("hello world", "hello", 0, 5),
            ("hello world", "lo", 0, 5),
            ("hello world", "", None, None),
            ("hello", "hello world", None, None),
            ("test", "st", -2, None),
        ]
        for s, suffix, start, end in test_cases:
            ls = L(s)
            if start is None and end is None:
                self.assertEqual(ls.endswith(suffix), s.endswith(suffix),
                               f"Failed for endswith({repr(suffix)})")
            elif end is None:
                self.assertEqual(ls.endswith(suffix, start), s.endswith(suffix, start),
                               f"Failed for endswith({repr(suffix)}, {start})")
            else:
                self.assertEqual(ls.endswith(suffix, start, end), s.endswith(suffix, start, end),
                               f"Failed for endswith({repr(suffix)}, {start}, {end})")
    
    def test_type_error(self):
        """Test that invalid types raise TypeError."""
        with self.assertRaises(TypeError):
            L("hello").endswith(123)
        with self.assertRaises(TypeError):
            L("hello").endswith(None)


class TestStartsEndsWithBufferTypes(unittest.TestCase):
    """Test startswith/endswith work correctly with different buffer types."""
    
    def test_slice_buffer(self):
        """Test with SliceBuffer."""
        s = L("xxxhello worldxxx")[3:-3]
        self.assertTrue(s.startswith("hello"))
        self.assertTrue(s.endswith("world"))
        self.assertFalse(s.startswith("xxx"))
    
    def test_join_buffer(self):
        """Test with JoinBuffer."""
        s = L("hello") + L(" ") + L("world")
        self.assertTrue(s.startswith("hello"))
        self.assertTrue(s.endswith("world"))
        self.assertTrue(s.startswith("hello ", 0, 6))
    
    def test_mul_buffer(self):
        """Test with MulBuffer."""
        s = L("abc") * 3
        self.assertTrue(s.startswith("abc"))
        self.assertTrue(s.endswith("abc"))
        self.assertTrue(s.startswith("abcabc"))
        self.assertTrue(s.endswith("bcabc"))


if __name__ == '__main__':
    unittest.main()
