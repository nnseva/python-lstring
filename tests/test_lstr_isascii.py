#!/usr/bin/env python3
"""
Tests for L.isascii() method.
"""

import unittest
from lstring import L
import lstring


class TestLStrIsascii(unittest.TestCase):
    """Tests for L.isascii() method."""
    
    @classmethod
    def setUpClass(cls):
        cls._orig_thresh = lstring.get_optimize_threshold()
        # disable C-level automatic collapsing/optimization for deterministic behavior
        lstring.set_optimize_threshold(0)

    @classmethod
    def tearDownClass(cls):
        lstring.set_optimize_threshold(cls._orig_thresh)
    
    def test_isascii_empty(self):
        """Empty string is ASCII."""
        self.assertTrue(L('').isascii())
        self.assertEqual(L('').isascii(), ''.isascii())
    
    def test_isascii_basic_ascii(self):
        """Basic ASCII characters (letters, digits, symbols)."""
        self.assertTrue(L('abc').isascii())
        self.assertTrue(L('ABC').isascii())
        self.assertTrue(L('123').isascii())
        self.assertTrue(L('Hello, World!').isascii())
        self.assertTrue(L(' \t\n\r').isascii())
        
        # Compare with str.isascii()
        self.assertEqual(L('abc').isascii(), 'abc'.isascii())
        self.assertEqual(L('Hello, World!').isascii(), 'Hello, World!'.isascii())
    
    def test_isascii_all_ascii_range(self):
        """All characters in ASCII range [0, 128)."""
        # Characters from 0x00 to 0x7F
        ascii_chars = ''.join(chr(i) for i in range(128))
        self.assertTrue(L(ascii_chars).isascii())
        self.assertEqual(L(ascii_chars).isascii(), ascii_chars.isascii())
    
    def test_isascii_non_ascii_unicode(self):
        """Non-ASCII Unicode characters."""
        self.assertFalse(L('привет').isascii())  # Cyrillic
        self.assertFalse(L('你好').isascii())      # Chinese
        self.assertFalse(L('café').isascii())     # Latin with accent
        self.assertFalse(L('naïve').isascii())    # Latin with diaeresis
        self.assertFalse(L('日本語').isascii())    # Japanese
        
        # Compare with str.isascii()
        self.assertEqual(L('привет').isascii(), 'привет'.isascii())
        self.assertEqual(L('café').isascii(), 'café'.isascii())
    
    def test_isascii_mixed(self):
        """Mixed ASCII and non-ASCII."""
        self.assertFalse(L('Hello мир').isascii())  # ASCII + Cyrillic
        self.assertFalse(L('test café').isascii())  # ASCII + accented
        self.assertFalse(L('a\u00e9b').isascii())   # a + é + b
        
        # Compare with str.isascii()
        self.assertEqual(L('Hello мир').isascii(), 'Hello мир'.isascii())
        self.assertEqual(L('test café').isascii(), 'test café'.isascii())
    
    def test_isascii_boundary(self):
        """Test boundary between ASCII (127) and non-ASCII (128)."""
        # 127 is DEL, last ASCII character
        self.assertTrue(L(chr(127)).isascii())
        self.assertEqual(L(chr(127)).isascii(), chr(127).isascii())
        
        # 128 is first non-ASCII character
        self.assertFalse(L(chr(128)).isascii())
        self.assertEqual(L(chr(128)).isascii(), chr(128).isascii())
        
        # String with character 127
        self.assertTrue(L('abc' + chr(127) + 'xyz').isascii())
        
        # String with character 128
        self.assertFalse(L('abc' + chr(128) + 'xyz').isascii())
    
    def test_isascii_special_unicode(self):
        """Special Unicode characters."""
        self.assertFalse(L('☺').isascii())        # Emoji
        self.assertFalse(L('™').isascii())        # Trademark symbol
        self.assertFalse(L('€').isascii())        # Euro sign
        self.assertFalse(L('λ').isascii())        # Greek lambda
        self.assertFalse(L('א').isascii())        # Hebrew aleph
        
        # Compare with str.isascii()
        self.assertEqual(L('☺').isascii(), '☺'.isascii())
        self.assertEqual(L('™').isascii(), '™'.isascii())
        self.assertEqual(L('€').isascii(), '€'.isascii())
    
    def test_isascii_lazy_string(self):
        """Test with lazy string (from operations)."""
        # Concatenation
        s = L('abc') + L('def')
        self.assertTrue(s.isascii())
        
        s = L('abc') + L('привет')
        self.assertFalse(s.isascii())
        
        # Multiplication
        s = L('abc') * 3
        self.assertTrue(s.isascii())
        
        s = L('café') * 2
        self.assertFalse(s.isascii())
        
        # Slice
        s = L('Hello, World!')[0:5]
        self.assertTrue(s.isascii())
        
        s = L('Hello, мир!')[0:10]
        self.assertFalse(s.isascii())
    
    def test_isascii_after_operations(self):
        """Test isascii after various string operations."""
        # upper/lower
        s = L('hello').upper()
        self.assertTrue(s.isascii())
        
        s = L('ПРИВЕТ').lower()
        self.assertFalse(s.isascii())
        
        # strip
        s = L('  spaces  ').strip()
        self.assertTrue(s.isascii())
        
        # replace
        s = L('hello').replace('l', 'L')
        self.assertTrue(s.isascii())
        
        s = L('hello').replace('h', 'п')  # Replace with Cyrillic
        self.assertFalse(s.isascii())
    
    def test_isascii_consistency_with_python(self):
        """Ensure L.isascii() matches str.isascii() for various inputs."""
        test_strings = [
            '',
            'a',
            'abc123',
            'Hello, World!',
            ' \t\n',
            chr(0),
            chr(127),
            chr(128),
            'café',
            'naïve',
            '你好',
            '😀',
            'abc' + chr(200) + 'xyz',
            'Test\u00e9',  # Test + é
        ]
        
        for s in test_strings:
            with self.subTest(s=repr(s)):
                self.assertEqual(L(s).isascii(), s.isascii(),
                                f"Mismatch for {repr(s)}")
    
    def test_isascii_mulbuffer(self):
        """Test isascii with MulBuffer (repeated strings)."""
        # ASCII repeated
        s = L('abc') * 100
        self.assertTrue(s.isascii())
        self.assertEqual(s.isascii(), ('abc' * 100).isascii())
        
        # Non-ASCII repeated
        s = L('café') * 50
        self.assertFalse(s.isascii())
        self.assertEqual(s.isascii(), ('café' * 50).isascii())
        
        # Single character repeated
        s = L('x') * 1000
        self.assertTrue(s.isascii())
        
        s = L('é') * 1000
        self.assertFalse(s.isascii())


if __name__ == '__main__':
    unittest.main()
