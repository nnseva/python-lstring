"""
Tests for findcs and rfindcs methods
"""

import sys
import unittest

import lstring
from lstring import L


class TestLStrFindcs(unittest.TestCase):
    """Tests for findcs and rfindcs methods"""
    
    @classmethod
    def setUpClass(cls):
        cls._orig_thresh = lstring.get_optimize_threshold()
        # disable C-level automatic collapsing/optimization for deterministic behavior
        lstring.set_optimize_threshold(0)

    @classmethod
    def tearDownClass(cls):
        lstring.set_optimize_threshold(cls._orig_thresh)

    # ===== Tests for findcs =====
    
    def test_findcs_basic(self):
        """Test basic findcs functionality"""
        s = L('hello world')
        # Find first vowel
        self.assertEqual(s.findcs('aeiou'), 1)  # 'e' at index 1
        # Find first consonant
        self.assertEqual(s.findcs('bcdfghjklmnpqrstvwxyz'), 0)  # 'h' at index 0
        # No match
        self.assertEqual(s.findcs('xyz'), -1)
    
    def test_findcs_with_str(self):
        """Test findcs with str charset"""
        s = L('hello world')
        self.assertEqual(s.findcs('aeiou'), 1)
        self.assertEqual(s.findcs('world'), 2)  # 'l' at index 2
    
    def test_findcs_with_L(self):
        """Test findcs with L charset"""
        s = L('hello world')
        charset = L('aeiou')
        self.assertEqual(s.findcs(charset), 1)
    
    def test_findcs_with_start(self):
        """Test findcs with start parameter"""
        s = L('hello world')
        self.assertEqual(s.findcs('o', 0), 4)  # First 'o' at index 4
        self.assertEqual(s.findcs('o', 5), 7)  # Second 'o' at index 7
        self.assertEqual(s.findcs('o', 8), -1)  # No 'o' after index 8
    
    def test_findcs_with_start_end(self):
        """Test findcs with start and end parameters"""
        s = L('hello world')
        self.assertEqual(s.findcs('o', 0, 5), 4)  # First 'o' within range
        self.assertEqual(s.findcs('o', 0, 4), -1)  # No 'o' before index 4
        self.assertEqual(s.findcs('aeiou', 6, 10), 7)  # 'o' at index 7
    
    def test_findcs_negative_indices(self):
        """Test findcs with negative indices"""
        s = L('hello world')
        # -5 from end is index 6 ('w')
        self.assertEqual(s.findcs('aeiou', -5), 7)  # 'o' at index 7
        # -3 from end is index 8 ('r'), so range [0, 8) contains 'e' at 1 and 'o' at 4
        self.assertEqual(s.findcs('aeiou', 0, -3), 1)  # First vowel 'e' at index 1
    
    def test_findcs_empty_charset(self):
        """Test findcs with empty charset"""
        s = L('hello world')
        self.assertEqual(s.findcs(''), -1)
        self.assertEqual(s.findcs(L('')), -1)
    
    def test_findcs_empty_string(self):
        """Test findcs on empty string"""
        s = L('')
        self.assertEqual(s.findcs('abc'), -1)
    
    def test_findcs_single_char(self):
        """Test findcs with single character charset"""
        s = L('hello world')
        self.assertEqual(s.findcs('o'), 4)
        self.assertEqual(s.findcs('x'), -1)
    
    def test_findcs_multiple_matches(self):
        """Test findcs finds first match"""
        s = L('aabbccdd')
        self.assertEqual(s.findcs('bcd'), 2)  # First 'b'
        self.assertEqual(s.findcs('dcba'), 0)  # First 'a'

    # ===== Tests for rfindcs =====
    
    def test_rfindcs_basic(self):
        """Test basic rfindcs functionality"""
        s = L('hello world')
        # Find last vowel
        self.assertEqual(s.rfindcs('aeiou'), 7)  # 'o' at index 7
        # Find last consonant
        self.assertEqual(s.rfindcs('bcdfghjklmnpqrstvwxyz'), 10)  # 'd' at index 10
        # No match
        self.assertEqual(s.rfindcs('xyz'), -1)
    
    def test_rfindcs_with_str(self):
        """Test rfindcs with str charset"""
        s = L('hello world')
        self.assertEqual(s.rfindcs('aeiou'), 7)
        self.assertEqual(s.rfindcs('world'), 10)  # 'd' at index 10
    
    def test_rfindcs_with_L(self):
        """Test rfindcs with L charset"""
        s = L('hello world')
        charset = L('aeiou')
        self.assertEqual(s.rfindcs(charset), 7)
    
    def test_rfindcs_with_start(self):
        """Test rfindcs with start parameter"""
        s = L('hello world')
        self.assertEqual(s.rfindcs('o', 0), 7)  # Last 'o' at index 7
        self.assertEqual(s.rfindcs('o', 5), 7)  # Last 'o' from index 5
        self.assertEqual(s.rfindcs('e', 5), -1)  # No 'e' from index 5 onward
    
    def test_rfindcs_with_start_end(self):
        """Test rfindcs with start and end parameters"""
        s = L('hello world')
        self.assertEqual(s.rfindcs('o', 0, 8), 7)  # Last 'o' before index 8
        self.assertEqual(s.rfindcs('o', 0, 5), 4)  # Last 'o' before index 5
        self.assertEqual(s.rfindcs('aeiou', 0, 6), 4)  # 'o' at index 4
    
    def test_rfindcs_negative_indices(self):
        """Test rfindcs with negative indices"""
        s = L('hello world')
        # -5 from end is index 6 ('w')
        self.assertEqual(s.rfindcs('aeiou', -5), 7)  # 'o' at index 7
        # -3 from end is index 8 ('r')
        self.assertEqual(s.rfindcs('aeiou', 0, -3), 7)  # 'o' at index 7
    
    def test_rfindcs_empty_charset(self):
        """Test rfindcs with empty charset"""
        s = L('hello world')
        self.assertEqual(s.rfindcs(''), -1)
        self.assertEqual(s.rfindcs(L('')), -1)
    
    def test_rfindcs_empty_string(self):
        """Test rfindcs on empty string"""
        s = L('')
        self.assertEqual(s.rfindcs('abc'), -1)
    
    def test_rfindcs_single_char(self):
        """Test rfindcs with single character charset"""
        s = L('hello world')
        self.assertEqual(s.rfindcs('o'), 7)
        self.assertEqual(s.rfindcs('x'), -1)
    
    def test_rfindcs_multiple_matches(self):
        """Test rfindcs finds last match"""
        s = L('aabbccdd')
        self.assertEqual(s.rfindcs('abc'), 5)  # Last 'c'
        self.assertEqual(s.rfindcs('dcba'), 7)  # Last 'd'

    # ===== Comparison tests =====
    
    def test_single_match(self):
        """When there's only one match, both should return same index"""
        s = L('hello')
        self.assertEqual(s.findcs('o'), 4)
        self.assertEqual(s.rfindcs('o'), 4)
    
    def test_no_match(self):
        """When there's no match, both should return -1"""
        s = L('hello')
        self.assertEqual(s.findcs('xyz'), -1)
        self.assertEqual(s.rfindcs('xyz'), -1)
    
    def test_multiple_matches(self):
        """With multiple matches, should return different indices"""
        s = L('hello world')
        self.assertEqual(s.findcs('o'), 4)  # First 'o'
        self.assertEqual(s.rfindcs('o'), 7)  # Last 'o'
    
    def test_type_error(self):
        """Both should raise TypeError for invalid charset type"""
        s = L('hello')
        
        # Test with integer
        with self.assertRaises(TypeError):
            s.findcs(123)
        with self.assertRaises(TypeError):
            s.rfindcs(123)
        
        # Test with None
        with self.assertRaises(TypeError):
            s.findcs(None)
        with self.assertRaises(TypeError):
            s.rfindcs(None)
        
        # Test with object that has collapse method but is not L instance
        class FakeL:
            def collapse(self):
                pass
        
        with self.assertRaises(TypeError):
            s.findcs(FakeL())
        with self.assertRaises(TypeError):
            s.rfindcs(FakeL())

    # ===== Edge cases =====
    
    def test_charset_with_duplicates(self):
        """Charset with duplicate characters should work correctly"""
        s = L('hello world')
        self.assertEqual(s.findcs('oooo'), 4)  # Should find 'o'
        self.assertEqual(s.rfindcs('oooo'), 7)  # Should find last 'o'
    
    def test_unicode_characters(self):
        """Test with unicode characters"""
        s = L('привет мир')
        # Find first vowel (а, е, и, о, у, ы, э, ю, я)
        vowels = L('аеиоуыэюя')
        self.assertEqual(s.findcs(vowels), 2)  # 'и' at index 2
        self.assertEqual(s.rfindcs(vowels), 8)  # 'и' at index 8
    
    def test_all_characters_match(self):
        """When all characters are in charset"""
        s = L('abc')
        self.assertEqual(s.findcs('abcdef'), 0)
        self.assertEqual(s.rfindcs('abcdef'), 2)
    
    def test_overlapping_ranges(self):
        """Test with various overlapping start/end ranges"""
        s = L('abcdefgh')
        # Normal range
        self.assertEqual(s.findcs('def', 2, 6), 3)  # 'd'
        # Inverted range (start > end)
        self.assertEqual(s.findcs('abc', 5, 2), -1)
        # Out of bounds
        self.assertEqual(s.findcs('abc', 100, 200), -1)
    
    def test_iterable_charset_list(self):
        """Test with list as charset"""
        s = L('hello world')
        # List of characters
        self.assertEqual(s.findcs(['a', 'e', 'i', 'o', 'u']), 1)  # 'e' at index 1
        self.assertEqual(s.rfindcs(['a', 'e', 'i', 'o', 'u']), 7)  # 'o' at index 7
        # Empty list
        self.assertEqual(s.findcs([]), -1)
        self.assertEqual(s.rfindcs([]), -1)
    
    def test_iterable_charset_tuple(self):
        """Test with tuple as charset"""
        s = L('hello world')
        self.assertEqual(s.findcs(('h', 'w')), 0)  # 'h' at index 0
        self.assertEqual(s.rfindcs(('h', 'w')), 6)  # 'w' at index 6
    
    def test_iterable_charset_set(self):
        """Test with set as charset"""
        s = L('hello world')
        vowels = {'a', 'e', 'i', 'o', 'u'}
        self.assertEqual(s.findcs(vowels), 1)  # 'e' at index 1
        self.assertEqual(s.rfindcs(vowels), 7)  # 'o' at index 7
    
    def test_iterable_charset_dict(self):
        """Test with dict as charset (uses keys)"""
        s = L('hello world')
        # Dict keys are used as charset
        charset = {'h': 1, 'w': 2, 'd': 3}
        self.assertEqual(s.findcs(charset), 0)  # 'h' at index 0
        self.assertEqual(s.rfindcs(charset), 10)  # 'd' at index 10
    
    def test_iterable_charset_generator(self):
        """Test with generator as charset"""
        s = L('hello world')
        vowels_gen = (c for c in 'aeiou')
        self.assertEqual(s.findcs(vowels_gen), 1)  # 'e' at index 1
        # Create new generator for rfindcs
        vowels_gen2 = (c for c in 'aeiou')
        self.assertEqual(s.rfindcs(vowels_gen2), 7)  # 'o' at index 7
    
    def test_iterable_charset_range(self):
        """Test with range object (should fail gracefully or work with chr())"""
        s = L('ABC123')
        # Range of ASCII codes for digits '0'-'9' (48-57)
        # join will convert numbers to strings, which will be individual digits
        self.assertEqual(s.findcs(['1', '2', '3']), 3)  # '1' at index 3


if __name__ == '__main__':
    unittest.main()
