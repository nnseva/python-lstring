"""
Tests for L.zfill() method.
"""

import unittest
from lstring import L
import lstring


class TestZfill(unittest.TestCase):
    """Test zfill method."""
    
    @classmethod
    def setUpClass(cls):
        """Disable optimization for predictable lazy behavior across tests."""
        cls.original_threshold = lstring.get_optimize_threshold()
        lstring.set_optimize_threshold(0)

    @classmethod
    def tearDownClass(cls):
        """Restore optimization threshold after tests complete."""
        lstring.set_optimize_threshold(cls.original_threshold)
    
    def test_zfill_basic(self):
        """Test basic zero padding."""
        s = L('42')
        result = s.zfill(5)
        self.assertEqual(str(result), '00042')
    
    def test_zfill_negative_number(self):
        """Test zero padding with negative sign."""
        s = L('-42')
        result = s.zfill(5)
        self.assertEqual(str(result), '-0042')
    
    def test_zfill_positive_sign(self):
        """Test zero padding with positive sign."""
        s = L('+42')
        result = s.zfill(5)
        self.assertEqual(str(result), '+0042')
    
    def test_zfill_already_wide(self):
        """Test when string is already wide enough."""
        s = L('12345')
        result = s.zfill(3)
        self.assertEqual(str(result), '12345')
        # Should return same object
        self.assertIs(result, s)
    
    def test_zfill_exact_width(self):
        """Test when string is exactly the requested width."""
        s = L('123')
        result = s.zfill(3)
        self.assertEqual(str(result), '123')
        self.assertIs(result, s)
    
    def test_zfill_empty_string(self):
        """Test zero padding of empty string."""
        s = L('')
        result = s.zfill(5)
        self.assertEqual(str(result), '00000')
    
    def test_zfill_single_char(self):
        """Test zero padding of single character."""
        s = L('x')
        result = s.zfill(5)
        self.assertEqual(str(result), '0000x')
    
    def test_zfill_sign_only(self):
        """Test zero padding of sign only."""
        s = L('-')
        result = s.zfill(5)
        self.assertEqual(str(result), '-0000')
    
    def test_zfill_plus_only(self):
        """Test zero padding of plus sign only."""
        s = L('+')
        result = s.zfill(5)
        self.assertEqual(str(result), '+0000')
    
    def test_zfill_text(self):
        """Test zero padding of text."""
        s = L('hello')
        result = s.zfill(10)
        self.assertEqual(str(result), '00000hello')
    
    def test_zfill_text_with_minus(self):
        """Test text starting with minus."""
        s = L('-hello')
        result = s.zfill(10)
        self.assertEqual(str(result), '-0000hello')
    
    def test_zfill_width_zero(self):
        """Test zfill with width=0."""
        s = L('42')
        result = s.zfill(0)
        self.assertEqual(str(result), '42')
    
    def test_zfill_width_one(self):
        """Test zfill with width=1."""
        s = L('42')
        result = s.zfill(1)
        self.assertEqual(str(result), '42')
    
    def test_zfill_lazy_structure(self):
        """Test that zfill creates lazy structure."""
        s = L('42')
        result = s.zfill(5)
        repr_str = repr(result)
        # Should contain multiplication or concatenation
        self.assertTrue('*' in repr_str or '+' in repr_str,
                       f"Expected lazy structure in {repr_str}")


class TestZfillEdgeCases(unittest.TestCase):
    """Test edge cases for zfill."""
    
    @classmethod
    def setUpClass(cls):
        """Disable optimization for predictable lazy behavior across tests."""
        cls.original_threshold = lstring.get_optimize_threshold()
        lstring.set_optimize_threshold(0)

    @classmethod
    def tearDownClass(cls):
        """Restore optimization threshold after tests complete."""
        lstring.set_optimize_threshold(cls.original_threshold)
    
    def test_multiple_signs(self):
        """Test string with multiple signs (only first is treated as sign)."""
        s = L('+-42')
        result = s.zfill(6)
        # Only first char is sign
        self.assertEqual(str(result), '+00-42')
    
    def test_sign_in_middle(self):
        """Test when minus is not at start."""
        s = L('42-')
        result = s.zfill(5)
        # No sign at start, just pad normally
        self.assertEqual(str(result), '0042-')
    
    def test_unicode(self):
        """Test with unicode characters."""
        s = L('привет')
        result = s.zfill(10)
        self.assertEqual(str(result), '0000привет')
    
    def test_unicode_with_sign(self):
        """Test unicode with sign."""
        s = L('-привет')
        result = s.zfill(10)
        self.assertEqual(str(result), '-000привет')
    
    def test_comparison_with_str(self):
        """Test that result matches Python's str.zfill."""
        test_cases = [
            ('42', 5),
            ('-42', 5),
            ('+42', 5),
            ('hello', 10),
            ('-hello', 10),
            ('', 5),
            ('x', 1),
            ('12345', 3),
            ('-', 5),
            ('+', 5),
        ]
        for text, width in test_cases:
            s = L(text)
            result = str(s.zfill(width))
            expected = text.zfill(width)
            self.assertEqual(result, expected,
                           f"Failed for text={repr(text)}, width={width}")
    
    def test_large_width(self):
        """Test with very large width."""
        s = L('x')
        result = s.zfill(100)
        self.assertEqual(len(result), 100)
        self.assertEqual(str(result), '0' * 99 + 'x')
    
    def test_negative_with_spaces(self):
        """Test that spaces are not treated as part of number."""
        s = L('- 42')
        result = s.zfill(6)
        # Space after sign means sign is still treated as sign
        self.assertEqual(str(result), '-00 42')
    
    def test_float_string(self):
        """Test with float representation."""
        s = L('3.14')
        result = s.zfill(6)
        self.assertEqual(str(result), '003.14')
    
    def test_negative_float_string(self):
        """Test with negative float representation."""
        s = L('-3.14')
        result = s.zfill(7)
        self.assertEqual(str(result), '-003.14')


if __name__ == '__main__':
    unittest.main()
