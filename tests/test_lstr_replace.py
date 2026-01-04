"""
Tests for replace() method.
"""
import unittest
from lstring import L
import lstring


class TestReplace(unittest.TestCase):
    """Tests for replace() method."""
    
    @classmethod
    def setUpClass(cls):
        cls._orig_thresh = lstring.get_optimize_threshold()
        # disable C-level automatic collapsing/optimization for deterministic behavior
        lstring.set_optimize_threshold(0)

    @classmethod
    def tearDownClass(cls):
        lstring.set_optimize_threshold(cls._orig_thresh)
    
    def test_basic_replace(self):
        """Basic replace with single occurrence."""
        self.assertEqual(L("hello world").replace("world", "Python"), L("hello Python"))
        self.assertEqual(L("hello world").replace("hello", "goodbye"), L("goodbye world"))
    
    def test_replace_multiple_occurrences(self):
        """Replace multiple occurrences."""
        self.assertEqual(L("hello hello").replace("hello", "hi"), L("hi hi"))
        self.assertEqual(L("the cat and the dog").replace("the", "a"), L("a cat and a dog"))
    
    def test_replace_single_char(self):
        """Replace single character."""
        self.assertEqual(L("hello world").replace("o", "X"), L("hellX wXrld"))
        self.assertEqual(L("aaa").replace("a", "b"), L("bbb"))
    
    def test_replace_not_found(self):
        """Replace when substring not found returns original."""
        result = L("hello").replace("goodbye", "hi")
        self.assertEqual(result, L("hello"))
    
    def test_replace_with_count(self):
        """Replace with count parameter."""
        self.assertEqual(L("hello hello hello").replace("hello", "hi", 1), L("hi hello hello"))
        self.assertEqual(L("hello hello hello").replace("hello", "hi", 2), L("hi hi hello"))
        self.assertEqual(L("aaa").replace("a", "b", 2), L("bba"))
    
    def test_replace_count_zero(self):
        """Replace with count=0 returns original."""
        result = L("hello").replace("hello", "hi", 0)
        self.assertEqual(result, L("hello"))
    
    def test_replace_count_exceeds_occurrences(self):
        """Replace with count exceeding occurrences."""
        self.assertEqual(L("hello hello").replace("hello", "hi", 10), L("hi hi"))
    
    def test_replace_with_empty_new(self):
        """Replace with empty string (deletion)."""
        self.assertEqual(L("hello world").replace("o", ""), L("hell wrld"))
        self.assertEqual(L("aaa").replace("a", ""), L(""))
    
    def test_replace_with_longer_string(self):
        """Replace with longer string."""
        self.assertEqual(L("hi").replace("hi", "hello"), L("hello"))
        self.assertEqual(L("a b").replace(" ", "___"), L("a___b"))
    
    def test_replace_whole_string(self):
        """Replace whole string."""
        self.assertEqual(L("hello").replace("hello", "world"), L("world"))
    
    def test_replace_at_boundaries(self):
        """Replace at string boundaries."""
        self.assertEqual(L("hello").replace("h", "H"), L("Hello"))
        self.assertEqual(L("hello").replace("o", "O"), L("hellO"))
    
    def test_replace_consecutive_occurrences(self):
        """Replace consecutive occurrences."""
        self.assertEqual(L("aaa").replace("a", "b"), L("bbb"))
        self.assertEqual(L("aaaa").replace("aa", "b"), L("bb"))
    
    def test_replace_with_L_instances(self):
        """Replace with L instances."""
        self.assertEqual(L("hello").replace(L("hello"), L("world")), L("world"))
        self.assertEqual(L("test").replace(L("t"), L("T")), L("TesT"))
    
    def test_replace_empty_old_raises(self):
        """Replace with empty old substring raises ValueError."""
        with self.assertRaises(ValueError) as cm:
            L("hello").replace("", "x")
        self.assertEqual(str(cm.exception), "replace() cannot replace empty substring")
    
    def test_comparison_with_str(self):
        """Compare behavior with Python str."""
        test_cases = [
            ("hello world", "o", "X", -1),
            ("hello hello", "hello", "hi", -1),
            ("hello hello hello", "hello", "hi", 1),
            ("hello hello hello", "hello", "hi", 2),
            ("test", "t", "T", -1),
            ("aaa", "a", "b", 2),
            ("hello", "x", "y", -1),
            ("abc abc", "abc", "", -1),
        ]
        for s, old, new, count in test_cases:
            ls = L(s)
            if count == -1:
                self.assertEqual(str(ls.replace(old, new)), s.replace(old, new),
                               f"Failed for replace({repr(old)}, {repr(new)})")
            else:
                self.assertEqual(str(ls.replace(old, new, count)), s.replace(old, new, count),
                               f"Failed for replace({repr(old)}, {repr(new)}, {count})")
    
    def test_type_error(self):
        """Test that invalid types raise TypeError."""
        with self.assertRaises(TypeError):
            L("hello").replace(123, "x")
        with self.assertRaises(TypeError):
            L("hello").replace("x", 123)
        with self.assertRaises(TypeError):
            L("hello").replace(None, "x")


class TestReplaceBufferTypes(unittest.TestCase):
    """Test replace works correctly with different buffer types."""
    
    def test_slice_buffer(self):
        """Test with SliceBuffer."""
        s = L("xxxhello worldxxx")[3:-3]
        result = s.replace("world", "Python")
        self.assertEqual(result, L("hello Python"))
    
    def test_join_buffer(self):
        """Test with JoinBuffer."""
        s = L("hello") + L(" ") + L("world")
        result = s.replace("world", "Python")
        self.assertEqual(result, L("hello Python"))
    
    def test_mul_buffer(self):
        """Test with MulBuffer."""
        s = L("abc") * 3
        result = s.replace("b", "B")
        self.assertEqual(result, L("aBcaBcaBc"))


class TestReplaceEdgeCases(unittest.TestCase):
    """Edge case tests for replace."""
    
    def test_replace_overlapping_pattern(self):
        """Replace doesn't handle overlapping patterns."""
        # "aa" appears at positions 0, 1, 2 (overlapping)
        # But replace only replaces non-overlapping: 0 and 2
        self.assertEqual(L("aaaa").replace("aa", "b"), L("bb"))
    
    def test_replace_unicode(self):
        """Test with Unicode strings."""
        self.assertEqual(L("Привет мир").replace("мир", "world"), L("Привет world"))
        self.assertEqual(L("こんにちは").replace("こ", "コ"), L("コんにちは"))
    
    def test_replace_empty_string(self):
        """Replace on empty string."""
        result = L("").replace("a", "b")
        self.assertEqual(result, L(""))
    
    def test_replace_creates_lazy_structure(self):
        """Replace should create lazy structure, not materialize immediately."""
        # This tests the lazy nature - result should be an L instance
        result = L("hello world").replace("world", "Python")
        self.assertIsInstance(result, L)
        # Only when converted to str should it materialize
        self.assertEqual(str(result), "hello Python")
    
    def test_replace_multiple_chars_with_single(self):
        """Replace multiple chars with single char."""
        self.assertEqual(L("hello").replace("ll", "L"), L("heLo"))
        self.assertEqual(L("goodbye").replace("oo", "u"), L("gudbye"))
    
    def test_replace_single_char_with_multiple(self):
        """Replace single char with multiple chars."""
        self.assertEqual(L("hello").replace("o", "oo"), L("helloo"))
        self.assertEqual(L("test").replace("t", "tt"), L("ttestt"))
    
    def test_replace_at_start(self):
        """Replace at the start of string."""
        self.assertEqual(L("hello world").replace("hello", "Hi"), L("Hi world"))
    
    def test_replace_at_end(self):
        """Replace at the end of string."""
        self.assertEqual(L("hello world").replace("world", "Python"), L("hello Python"))
    
    def test_replace_entire_string(self):
        """Replace entire string."""
        self.assertEqual(L("test").replace("test", "replacement"), L("replacement"))
    
    def test_replace_with_itself(self):
        """Replace substring with itself."""
        result = L("hello").replace("hello", "hello")
        self.assertEqual(result, L("hello"))


class TestReplaceVsStrReplace(unittest.TestCase):
    """Comprehensive comparison with str.replace()."""
    
    def test_extensive_comparison(self):
        """Extensive test cases comparing with str.replace()."""
        test_strings = [
            "hello world",
            "the quick brown fox",
            "aaa",
            "aaaa",
            "test test test",
            "",
            "a",
            "abcdefghijklmnop",
        ]
        
        replacements = [
            ("a", "A"),
            ("test", "TEST"),
            ("o", "0"),
            (" ", "_"),
            ("aa", "b"),
            ("quick", "slow"),
        ]
        
        counts = [-1, 0, 1, 2, 100]
        
        for s in test_strings:
            for old, new in replacements:
                if old in s:  # Only test if old exists in string
                    for count in counts:
                        ls = L(s)
                        if count == -1:
                            self.assertEqual(str(ls.replace(old, new)), s.replace(old, new),
                                           f"Failed for {repr(s)}.replace({repr(old)}, {repr(new)})")
                        else:
                            self.assertEqual(str(ls.replace(old, new, count)), s.replace(old, new, count),
                                           f"Failed for {repr(s)}.replace({repr(old)}, {repr(new)}, {count})")


if __name__ == '__main__':
    unittest.main()
