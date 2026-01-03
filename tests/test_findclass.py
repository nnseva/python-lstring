#!/usr/bin/env python
"""Tests for findcc and rfindcc methods"""

import unittest
from lstring import L, CharClass


class TestFindCC(unittest.TestCase):
    """Test findcc method"""
    
    def test_findcc_space(self):
        """Test finding whitespace"""
        s = L('hello world')
        self.assertEqual(s.findcc(CharClass.SPACE), 5)
        
    def test_findcc_alpha(self):
        """Test finding alphabetic character"""
        s = L('123abc')
        self.assertEqual(s.findcc(CharClass.ALPHA), 3)
        
    def test_findcc_digit(self):
        """Test finding digit"""
        s = L('abc123')
        self.assertEqual(s.findcc(CharClass.DIGIT), 3)
        
    def test_findcc_not_found(self):
        """Test when character class not found"""
        s = L('abc')
        self.assertEqual(s.findcc(CharClass.DIGIT), -1)
        
    def test_findcc_invert(self):
        """Test finding character NOT in class"""
        s = L('   hello')
        self.assertEqual(s.findcc(CharClass.SPACE, invert=True), 3)
        
    def test_findcc_combined(self):
        """Test finding with combined character classes"""
        s = L('!!!abc')
        pos = s.findcc(CharClass.ALPHA | CharClass.DIGIT)
        self.assertEqual(pos, 3)
        
    def test_findcc_with_range(self):
        """Test findcc with start/end parameters"""
        s = L('ab cd ef')
        # Find space starting from position 3
        self.assertEqual(s.findcc(CharClass.SPACE, 3), 5)
        # Find within range that doesn't contain space
        self.assertEqual(s.findcc(CharClass.SPACE, 0, 2), -1)


class TestRFindCC(unittest.TestCase):
    """Test rfindcc method"""
    
    def test_rfindcc_space(self):
        """Test finding whitespace from right"""
        s = L('hello world test')
        self.assertEqual(s.rfindcc(CharClass.SPACE), 11)
        
    def test_rfindcc_alpha(self):
        """Test finding alphabetic character from right"""
        s = L('abc123')
        self.assertEqual(s.rfindcc(CharClass.ALPHA), 2)
        
    def test_rfindcc_digit(self):
        """Test finding digit from right"""
        s = L('123abc456')
        self.assertEqual(s.rfindcc(CharClass.DIGIT), 8)
        
    def test_rfindcc_not_found(self):
        """Test when character class not found"""
        s = L('abc')
        self.assertEqual(s.rfindcc(CharClass.DIGIT), -1)
        
    def test_rfindcc_invert(self):
        """Test finding character NOT in class from right"""
        s = L('hello   ')
        self.assertEqual(s.rfindcc(CharClass.SPACE, invert=True), 4)
        
    def test_rfindcc_with_range(self):
        """Test rfindcc with start/end parameters"""
        s = L('ab cd ef')
        # Find space from right up to position 6
        self.assertEqual(s.rfindcc(CharClass.SPACE, 0, 6), 5)
        # Find within range that doesn't contain space
        self.assertEqual(s.rfindcc(CharClass.SPACE, 0, 2), -1)


class TestFindCCEdgeCases(unittest.TestCase):
    """Test edge cases for findcc and rfindcc"""
    
    def test_empty_string(self):
        """Test on empty string"""
        s = L('')
        self.assertEqual(s.findcc(CharClass.ALPHA), -1)
        self.assertEqual(s.rfindcc(CharClass.ALPHA), -1)
        
    def test_single_char_match(self):
        """Test on single character that matches"""
        s = L('a')
        self.assertEqual(s.findcc(CharClass.ALPHA), 0)
        self.assertEqual(s.rfindcc(CharClass.ALPHA), 0)
        
    def test_single_char_no_match(self):
        """Test on single character that doesn't match"""
        s = L('5')
        self.assertEqual(s.findcc(CharClass.ALPHA), -1)
        self.assertEqual(s.rfindcc(CharClass.ALPHA), -1)
        
    def test_all_chars_match(self):
        """Test when all characters match"""
        s = L('abcdef')
        self.assertEqual(s.findcc(CharClass.ALPHA), 0)
        self.assertEqual(s.rfindcc(CharClass.ALPHA), 5)
        
    def test_negative_indices(self):
        """Test with negative start/end indices"""
        s = L('hello world')
        # Start from -5 (index 6)
        self.assertEqual(s.findcc(CharClass.ALPHA, -5), 6)
        # End at -5 (index 6)
        self.assertEqual(s.rfindcc(CharClass.ALPHA, 0, -5), 4)


class TestCharClassCombinations(unittest.TestCase):
    """Test different character class combinations"""
    
    def test_alnum(self):
        """Test ALNUM composite class"""
        s = L('!@#abc123')
        pos = s.findcc(CharClass.ALNUM)
        self.assertEqual(pos, 3)  # First alphanumeric is 'a'
        
    def test_alpha_or_digit(self):
        """Test ALPHA | DIGIT"""
        s = L('   a')
        pos = s.findcc(CharClass.ALPHA | CharClass.DIGIT)
        self.assertEqual(pos, 3)
        
    def test_lower_and_upper(self):
        """Test finding lower or upper case"""
        s = L('123Hello')
        pos_lower = s.findcc(CharClass.LOWER)
        pos_upper = s.findcc(CharClass.UPPER)
        self.assertEqual(pos_lower, 4)  # 'e'
        self.assertEqual(pos_upper, 3)  # 'H'
        
    def test_printable(self):
        """Test printable character class"""
        s = L('hello')
        # All normal chars are printable
        self.assertEqual(s.findcc(CharClass.PRINTABLE), 0)


if __name__ == '__main__':
    unittest.main()
