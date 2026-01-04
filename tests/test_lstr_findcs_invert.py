"""
Тесты для параметра invert в findcs/rfindcs.
"""

import unittest
from lstring import L
import lstring

class TestFindcsInvert(unittest.TestCase):
    """Test findcs with invert parameter."""

    @classmethod
    def setUpClass(cls):
        cls._orig_thresh = lstring.get_optimize_threshold()
        # disable C-level automatic collapsing/optimization for deterministic behavior
        lstring.set_optimize_threshold(0)

    @classmethod
    def tearDownClass(cls):
        lstring.set_optimize_threshold(cls._orig_thresh)
   
    def test_findcs_without_invert(self):
        """Test findcs finds character in charset."""
        s = L('hello world')
        # Find first vowel
        pos = s.findcs('aeiou')
        self.assertEqual(pos, 1)  # 'e' at position 1
        self.assertEqual(str(s[pos:pos+1]), 'e')
    
    def test_findcs_with_invert(self):
        """Test findcs with invert=True finds character NOT in charset."""
        s = L('hello world')
        # Find first consonant
        pos = s.findcs('aeiou', invert=True)
        self.assertEqual(pos, 0)  # 'h' at position 0
        self.assertEqual(str(s[pos:pos+1]), 'h')
    
    def test_findcs_invert_no_match(self):
        """Test findcs with invert when all characters are in charset."""
        s = L('aeiou')
        pos = s.findcs('aeiou', invert=True)
        self.assertEqual(pos, -1)  # No character NOT in 'aeiou'
    
    def test_findcs_invert_empty_charset(self):
        """Test findcs with invert and empty charset returns first position."""
        s = L('hello')
        pos = s.findcs('', invert=True)
        self.assertEqual(pos, 0)  # Empty charset, invert=True finds first char
    
    def test_findcs_invert_with_range(self):
        """Test findcs with invert within a range."""
        s = L('aaabbbccc')
        # Find first non-'a' after position 0
        pos = s.findcs('a', 0, 9, invert=True)
        self.assertEqual(pos, 3)  # First 'b' at position 3


class TestRfindcsInvert(unittest.TestCase):
    """Test rfindcs with invert parameter."""

    @classmethod
    def setUpClass(cls):
        cls._orig_thresh = lstring.get_optimize_threshold()
        # disable C-level automatic collapsing/optimization for deterministic behavior
        lstring.set_optimize_threshold(0)

    @classmethod
    def tearDownClass(cls):
        lstring.set_optimize_threshold(cls._orig_thresh)
    
    def test_rfindcs_without_invert(self):
        """Test rfindcs finds character in charset."""
        s = L('hello world')
        # Find last vowel
        pos = s.rfindcs('aeiou')
        self.assertEqual(pos, 7)  # 'o' at position 7
        self.assertEqual(str(s[pos:pos+1]), 'o')
    
    def test_rfindcs_with_invert(self):
        """Test rfindcs with invert=True finds character NOT in charset."""
        s = L('hello world')
        # Find last consonant
        pos = s.rfindcs('aeiou', invert=True)
        self.assertEqual(pos, 10)  # 'd' at position 10
        self.assertEqual(str(s[pos:pos+1]), 'd')
    
    def test_rfindcs_invert_no_match(self):
        """Test rfindcs with invert when all characters are in charset."""
        s = L('aeiou')
        pos = s.rfindcs('aeiou', invert=True)
        self.assertEqual(pos, -1)  # No character NOT in 'aeiou'
    
    def test_rfindcs_invert_empty_charset(self):
        """Test rfindcs with invert and empty charset returns last position."""
        s = L('hello')
        pos = s.rfindcs('', invert=True)
        self.assertEqual(pos, 4)  # Empty charset, invert=True finds last char
    
    def test_rfindcs_invert_with_range(self):
        """Test rfindcs with invert within a range."""
        s = L('aaabbbccc')
        # Find last non-'c' before end
        pos = s.rfindcs('c', 0, 9, invert=True)
        self.assertEqual(pos, 5)  # Last 'b' at position 5


class TestStripWithFindcsInvert(unittest.TestCase):
    """Test that strip methods use findcs/rfindcs with invert correctly."""

    @classmethod
    def setUpClass(cls):
        cls._orig_thresh = lstring.get_optimize_threshold()
        # disable C-level automatic collapsing/optimization for deterministic behavior
        lstring.set_optimize_threshold(0)

    @classmethod
    def tearDownClass(cls):
        lstring.set_optimize_threshold(cls._orig_thresh)

    def test_lstrip_uses_findcs_invert(self):
        """Test lstrip correctly uses findcs with invert."""
        s = L('---===hello')
        result = s.lstrip('-=')
        self.assertEqual(str(result), 'hello')
        # Should be a slice starting at position 6
        repr_str = repr(result)
        self.assertIn('[6:', repr_str)
    
    def test_rstrip_uses_rfindcs_invert(self):
        """Test rstrip correctly uses rfindcs with invert."""
        s = L('hello===---')
        result = s.rstrip('-=')
        self.assertEqual(str(result), 'hello')
        # Should be a slice ending at position 5
        repr_str = repr(result)
        self.assertIn('[0:5]', repr_str)
    
    def test_strip_combines_both(self):
        """Test strip uses both findcs and rfindcs with invert."""
        s = L('---===hello===---')
        result = s.strip('-=')
        self.assertEqual(str(result), 'hello')
        # Should have single slice with both boundaries
        repr_str = repr(result)
        # One slice operation with both start and end
        self.assertEqual(repr_str.count('['), 1)
        # Should contain both boundaries like [6:11]
        self.assertIn('[6:11]', repr_str)
    
    def test_strip_all_chars_to_remove(self):
        """Test strip when entire string should be removed."""
        s = L('---===')
        result = s.strip('-=')
        self.assertEqual(str(result), '')
        self.assertEqual(len(result), 0)
    
    def test_strip_no_chars_to_remove(self):
        """Test strip when no characters should be removed."""
        s = L('hello')
        result = s.strip('-=')
        self.assertIs(result, s)  # Should return same object
        self.assertEqual(str(result), 'hello')
    
    def test_strip_mixed_chars(self):
        """Test strip with multiple different characters."""
        s = L('.,;hello world.,;')
        result = s.strip('.,;')
        self.assertEqual(str(result), 'hello world')


if __name__ == '__main__':
    unittest.main()
