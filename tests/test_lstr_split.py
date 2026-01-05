"""
Tests for L.split() and L.rsplit() methods
"""

import unittest
from lstring import L
import lstring


class TestSplit(unittest.TestCase):
    """Test L.split() method"""
    
    @classmethod
    def setUpClass(cls):
        cls._orig_thresh = lstring.get_optimize_threshold()
        # disable C-level automatic collapsing/optimization for deterministic behavior
        lstring.set_optimize_threshold(0)

    @classmethod
    def tearDownClass(cls):
        lstring.set_optimize_threshold(cls._orig_thresh)
    
    def test_split_basic(self):
        """Basic split with separator."""
        self.assertEqual(L("a,b,c").split(','), [L('a'), L('b'), L('c')])
    
    def test_split_no_separator(self):
        """Split with no separator found."""
        self.assertEqual(L("hello").split(','), [L('hello')])
    
    def test_split_empty_segments(self):
        """Split creates empty segments between consecutive separators."""
        self.assertEqual(L("a,,b").split(','), [L('a'), L(''), L('b')])
        self.assertEqual(L(",,").split(','), [L(''), L(''), L('')])
    
    def test_split_at_boundaries(self):
        """Split at string boundaries."""
        self.assertEqual(L(",a,b").split(','), [L(''), L('a'), L('b')])
        self.assertEqual(L("a,b,").split(','), [L('a'), L('b'), L('')])
    
    def test_split_with_maxsplit(self):
        """Split with maxsplit parameter."""
        self.assertEqual(L("a,b,c,d").split(',', 1), [L('a'), L('b,c,d')])
        self.assertEqual(L("a,b,c,d").split(',', 2), [L('a'), L('b'), L('c,d')])
    
    def test_split_maxsplit_zero(self):
        """Split with maxsplit=0 returns original string in list."""
        self.assertEqual(L("a,b,c").split(',', 0), [L('a,b,c')])
    
    def test_split_whitespace(self):
        """Split by whitespace (sep=None)."""
        self.assertEqual(L("a b c").split(), [L('a'), L('b'), L('c')])
        self.assertEqual(L("a  b  c").split(), [L('a'), L('b'), L('c')])  # Multiple spaces
        self.assertEqual(L("  a  b  ").split(), [L('a'), L('b')])  # Leading/trailing
        self.assertEqual(L("a\tb\nc").split(), [L('a'), L('b'), L('c')])  # Mixed whitespace
    
    def test_split_whitespace_with_maxsplit(self):
        """Split by whitespace with maxsplit."""
        self.assertEqual(L("a b c d").split(None, 1), [L('a'), L('b c d')])
        self.assertEqual(L("a  b  c  d").split(None, 2), [L('a'), L('b'), L('c  d')])
    
    def test_split_whitespace_maxsplit_no_trailing_space(self):
        """Split by whitespace with maxsplit when string ends without space."""
        # This covers the edge case where space == -1 in split() loop
        self.assertEqual(L("a b c").split(None, 1), [L('a'), L('b c')])
        self.assertEqual(L("a b c").split(None, 2), [L('a'), L('b'), L('c')])
        self.assertEqual(L("word1 word2").split(None, 1), [L('word1'), L('word2')])
        # maxsplit larger than actual number of segments - hits space == -1 case
        self.assertEqual(L("a b c").split(None, 10), [L('a'), L('b'), L('c')])
        self.assertEqual(L("word").split(None, 5), [L('word')])
        # Edge case: leading spaces, word at end - hits pos >= length case (line 711)
        self.assertEqual(L("  a").split(None, 10), [L('a')])
        self.assertEqual(L("   word").split(None, 5), [L('word')])
    
    def test_split_empty_string(self):
        """Split empty string."""
        self.assertEqual(L("").split(','), [L('')])
        self.assertEqual(L("").split(), [])
        self.assertEqual(L("   ").split(), [])  # Only whitespace
    
    def test_split_multichar_separator(self):
        """Split with multi-character separator."""
        self.assertEqual(L("a::b::c").split('::'), [L('a'), L('b'), L('c')])
        self.assertEqual(L("hello world hello").split('hello'), [L(''), L(' world '), L('')])
    
    def test_split_with_L_separator(self):
        """Split with L instance as separator."""
        self.assertEqual(L("a,b,c").split(L(',')), [L('a'), L('b'), L('c')])
    
    def test_split_empty_separator_raises(self):
        """Split with empty separator raises ValueError."""
        with self.assertRaises(ValueError):
            L("hello").split('')
    
    def test_split_type_error(self):
        """Split with invalid type raises TypeError."""
        with self.assertRaises(TypeError):
            L("hello").split(123)


class TestRSplit(unittest.TestCase):
    """Test L.rsplit() method"""
    
    def test_rsplit_basic(self):
        """Basic rsplit with separator."""
        self.assertEqual(L("a,b,c").rsplit(','), [L('a'), L('b'), L('c')])
    
    def test_rsplit_no_separator(self):
        """RSplit with no separator found."""
        self.assertEqual(L("hello").rsplit(','), [L('hello')])
    
    def test_rsplit_empty_segments(self):
        """RSplit creates empty segments between consecutive separators."""
        self.assertEqual(L("a,,b").rsplit(','), [L('a'), L(''), L('b')])
    
    def test_rsplit_at_boundaries(self):
        """RSplit at string boundaries."""
        self.assertEqual(L(",a,b").rsplit(','), [L(''), L('a'), L('b')])
        self.assertEqual(L("a,b,").rsplit(','), [L('a'), L('b'), L('')])
    
    def test_rsplit_with_maxsplit(self):
        """RSplit with maxsplit parameter (splits from right)."""
        self.assertEqual(L("a,b,c,d").rsplit(',', 1), [L('a,b,c'), L('d')])
        self.assertEqual(L("a,b,c,d").rsplit(',', 2), [L('a,b'), L('c'), L('d')])
    
    def test_rsplit_maxsplit_zero(self):
        """RSplit with maxsplit=0 returns original string in list."""
        self.assertEqual(L("a,b,c").rsplit(',', 0), [L('a,b,c')])
    
    def test_rsplit_whitespace(self):
        """RSplit by whitespace (sep=None)."""
        self.assertEqual(L("a b c").rsplit(), [L('a'), L('b'), L('c')])
        self.assertEqual(L("a  b  c").rsplit(), [L('a'), L('b'), L('c')])
        self.assertEqual(L("  a  b  ").rsplit(), [L('a'), L('b')])
    
    def test_rsplit_whitespace_with_maxsplit(self):
        """RSplit by whitespace with maxsplit."""
        self.assertEqual(L("a b c d").rsplit(None, 1), [L('a b c'), L('d')])
        self.assertEqual(L("a  b  c  d").rsplit(None, 2), [L('a  b'), L('c'), L('d')])
    
    def test_rsplit_whitespace_maxsplit_no_leading_space(self):
        """RSplit by whitespace with maxsplit when string starts without space."""
        # This covers the edge case where space == -1 in rsplit() loop
        self.assertEqual(L("a b c").rsplit(None, 1), [L('a b'), L('c')])
        self.assertEqual(L("a b c").rsplit(None, 2), [L('a'), L('b'), L('c')])
        self.assertEqual(L("word1 word2").rsplit(None, 1), [L('word1'), L('word2')])
        # maxsplit larger than actual number of segments - hits space == -1 case
        self.assertEqual(L("a b c").rsplit(None, 10), [L('a'), L('b'), L('c')])
        self.assertEqual(L("word").rsplit(None, 5), [L('word')])
        # Edge case: word at start, trailing spaces - hits pos <= 0 case (line 830)
        self.assertEqual(L("a  ").rsplit(None, 10), [L('a')])
        self.assertEqual(L("word   ").rsplit(None, 5), [L('word')])
    
    def test_rsplit_empty_string(self):
        """RSplit empty string."""
        self.assertEqual(L("").rsplit(','), [L('')])
        self.assertEqual(L("").rsplit(), [])
    
    def test_rsplit_multichar_separator(self):
        """RSplit with multi-character separator."""
        self.assertEqual(L("a::b::c").rsplit('::'), [L('a'), L('b'), L('c')])
    
    def test_rsplit_with_L_separator(self):
        """RSplit with L instance as separator."""
        self.assertEqual(L("a,b,c").rsplit(L(',')), [L('a'), L('b'), L('c')])
    
    def test_rsplit_empty_separator_raises(self):
        """RSplit with empty separator raises ValueError."""
        with self.assertRaises(ValueError):
            L("hello").rsplit('')
    
    def test_rsplit_type_error(self):
        """RSplit with invalid type raises TypeError."""
        with self.assertRaises(TypeError):
            L("hello").rsplit(123)


class TestSplitVsStrSplit(unittest.TestCase):
    """Compare L.split() behavior with str.split()"""
    
    def test_comparison_split(self):
        """Extensive comparison of split() with str.split()."""
        test_cases = [
            ("a,b,c", ",", -1),
            ("a,,b", ",", -1),
            (",a,", ",", -1),
            ("a,b,c,d", ",", 2),
            ("hello world", " ", -1),
            ("a  b  c", None, -1),
            ("  a  b  ", None, -1),
            ("", ",", -1),
            ("hello", ",", -1),
        ]
        
        for string, sep, maxsplit in test_cases:
            with self.subTest(string=string, sep=sep, maxsplit=maxsplit):
                l_result = L(string).split(sep, maxsplit)
                str_result = string.split(sep, maxsplit)
                
                self.assertEqual(len(l_result), len(str_result))
                for l_item, str_item in zip(l_result, str_result):
                    self.assertEqual(str(l_item), str_item)
    
    def test_comparison_rsplit(self):
        """Extensive comparison of rsplit() with str.rsplit()."""
        test_cases = [
            ("a,b,c", ",", -1),
            ("a,,b", ",", -1),
            (",a,", ",", -1),
            ("a,b,c,d", ",", 2),
            ("hello world", " ", -1),
            ("a  b  c", None, -1),
            ("  a  b  ", None, -1),
            ("", ",", -1),
            ("hello", ",", -1),
        ]
        
        for string, sep, maxsplit in test_cases:
            with self.subTest(string=string, sep=sep, maxsplit=maxsplit):
                l_result = L(string).rsplit(sep, maxsplit)
                str_result = string.rsplit(sep, maxsplit)
                
                self.assertEqual(len(l_result), len(str_result))
                for l_item, str_item in zip(l_result, str_result):
                    self.assertEqual(str(l_item), str_item)


class TestSplitBufferTypes(unittest.TestCase):
    """Test split/rsplit with different buffer types"""
    
    def test_split_join_buffer(self):
        """Split on JoinBuffer."""
        s = L("a,b") + L(",c")
        result = s.split(',')
        self.assertEqual(result, [L('a'), L('b'), L('c')])
    
    def test_split_mul_buffer(self):
        """Split on MulBuffer."""
        s = L("a,") * 3
        result = s.split(',')
        self.assertEqual(result, [L('a'), L('a'), L('a'), L('')])
    
    def test_split_slice_buffer(self):
        """Split on SliceBuffer."""
        s = L("_a,b,c_")[1:-1]
        result = s.split(',')
        self.assertEqual(result, [L('a'), L('b'), L('c')])


class TestSplitIterators(unittest.TestCase):
    """Test L.split_iter() and L.rsplit_iter() generator methods"""
    
    def test_split_iter_returns_generator(self):
        """Test that split_iter returns a generator."""
        result = L('a,b,c').split_iter(',')
        self.assertTrue(hasattr(result, '__iter__') and hasattr(result, '__next__'))
        self.assertEqual(list(result), [L('a'), L('b'), L('c')])
    
    def test_rsplit_iter_returns_generator(self):
        """Test that rsplit_iter returns a generator."""
        result = L('a,b,c').rsplit_iter(',', 1)
        self.assertTrue(hasattr(result, '__iter__') and hasattr(result, '__next__'))
        # rsplit_iter yields from right to left, so we need to reverse
        self.assertEqual(list(reversed(list(result))), [L('a,b'), L('c')])
    
    def test_split_iter_whitespace(self):
        """Test that split_iter with sep=None returns a generator."""
        result = L('a  b  c').split_iter()
        self.assertTrue(hasattr(result, '__iter__') and hasattr(result, '__next__'))
        self.assertEqual(list(result), [L('a'), L('b'), L('c')])
    
    def test_rsplit_iter_whitespace(self):
        """Test that rsplit_iter with sep=None returns a generator."""
        result = L('a  b  c').rsplit_iter(maxsplit=1)
        self.assertTrue(hasattr(result, '__iter__') and hasattr(result, '__next__'))
        # rsplit_iter yields from right to left
        self.assertEqual(list(reversed(list(result))), [L('a  b'), L('c')])
    
    def test_split_still_returns_list(self):
        """Test that split() still returns a list (not a generator)."""
        result = L('a,b,c').split(',')
        self.assertIsInstance(result, list)
        self.assertEqual(result, [L('a'), L('b'), L('c')])
    
    def test_rsplit_still_returns_list(self):
        """Test that rsplit() still returns a list (not a generator)."""
        result = L('a,b,c').rsplit(',', 1)
        self.assertIsInstance(result, list)
        self.assertEqual(result, [L('a,b'), L('c')])
    
    def test_split_iter_consistency_with_split(self):
        """Test that split_iter produces same results as split."""
        test_cases = [
            ('a,b,c', ',', -1),
            ('a  b  c', None, -1),
            ('a,b,c,d', ',', 2),
            ('  hello  world  ', None, 1),
        ]
        for string, sep, maxsplit in test_cases:
            with self.subTest(string=string, sep=sep, maxsplit=maxsplit):
                s = L(string)
                self.assertEqual(
                    list(s.split_iter(sep, maxsplit)),
                    s.split(sep, maxsplit)
                )
    
    def test_rsplit_iter_consistency_with_rsplit(self):
        """Test that rsplit_iter produces same results as rsplit (after reversal)."""
        test_cases = [
            ('a,b,c', ',', -1),
            ('a  b  c', None, -1),
            ('a,b,c,d', ',', 2),
            ('  hello  world  ', None, 1),
        ]
        for string, sep, maxsplit in test_cases:
            with self.subTest(string=string, sep=sep, maxsplit=maxsplit):
                s = L(string)
                self.assertEqual(
                    list(reversed(list(s.rsplit_iter(sep, maxsplit)))),
                    s.rsplit(sep, maxsplit)
                )


if __name__ == '__main__':
    unittest.main()
