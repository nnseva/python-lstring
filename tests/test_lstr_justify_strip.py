"""
Tests for L.ljust(), L.rjust(), L.center(), L.lstrip(), L.rstrip(), L.strip() methods.
These methods use lazy operations (multiplication for padding, slices for stripping).
"""

import unittest
from lstring import L


class TestLJust(unittest.TestCase):
    """Test L.ljust() method."""
    
    def test_ljust_basic(self):
        """Test basic left justification with default fillchar."""
        result = L('hello').ljust(10)
        self.assertEqual(str(result), 'hello     ')
        self.assertEqual(len(result), 10)
    
    def test_ljust_custom_fillchar(self):
        """Test left justification with custom fillchar."""
        result = L('hello').ljust(10, '-')
        self.assertEqual(str(result), 'hello-----')
        self.assertEqual(len(result), 10)
    
    def test_ljust_no_padding_needed(self):
        """Test when string is already wider than requested width."""
        s = L('hello world')
        result = s.ljust(5)
        self.assertEqual(str(result), 'hello world')
        self.assertIs(result, s)  # Should return same object
    
    def test_ljust_exact_width(self):
        """Test when string is exactly the requested width."""
        result = L('hello').ljust(5)
        self.assertEqual(str(result), 'hello')
    
    def test_ljust_lazy_structure(self):
        """Test that ljust creates lazy structure (not immediately materialized)."""
        import lstring
        lstring.set_optimize_threshold(0)  # Disable automatic optimization
        try:
            result = L('hello').ljust(10, '-')
            # Should be a join of original string and multiplication
            repr_str = repr(result)
            self.assertIn('+', repr_str)  # Should show concatenation
        finally:
            lstring.set_optimize_threshold(1024)  # Restore default


class TestRJust(unittest.TestCase):
    """Test L.rjust() method."""
    
    def test_rjust_basic(self):
        """Test basic right justification with default fillchar."""
        result = L('hello').rjust(10)
        self.assertEqual(str(result), '     hello')
        self.assertEqual(len(result), 10)
    
    def test_rjust_custom_fillchar(self):
        """Test right justification with custom fillchar."""
        result = L('hello').rjust(10, '-')
        self.assertEqual(str(result), '-----hello')
        self.assertEqual(len(result), 10)
    
    def test_rjust_no_padding_needed(self):
        """Test when string is already wider than requested width."""
        result = L('hello world').rjust(5)
        self.assertEqual(str(result), 'hello world')
    
    def test_rjust_lazy_structure(self):
        """Test that rjust creates lazy structure."""
        import lstring
        lstring.set_optimize_threshold(0)
        try:
            result = L('hello').rjust(10, '*')
            repr_str = repr(result)
            self.assertIn('+', repr_str)  # Should show concatenation
        finally:
            lstring.set_optimize_threshold(1024)


class TestCenter(unittest.TestCase):
    """Test L.center() method."""
    
    def test_center_basic_odd_padding(self):
        """Test centering with odd amount of padding (left gets less)."""
        result = L('hello').center(11)
        self.assertEqual(str(result), '   hello   ')
        self.assertEqual(len(result), 11)
    
    def test_center_basic_even_padding(self):
        """Test centering with even amount of padding."""
        result = L('hello').center(10)
        # With even padding (5 total), left gets 2, right gets 3
        self.assertEqual(str(result), '  hello   ')
        self.assertEqual(len(result), 10)
    
    def test_center_custom_fillchar(self):
        """Test centering with custom fillchar."""
        result = L('hello').center(10, '-')
        self.assertEqual(str(result), '--hello---')
        self.assertEqual(len(result), 10)
    
    def test_center_no_padding_needed(self):
        """Test when string is already wider than requested width."""
        result = L('hello world').center(5)
        self.assertEqual(str(result), 'hello world')
    
    def test_center_lazy_structure(self):
        """Test that center creates lazy structure."""
        import lstring
        lstring.set_optimize_threshold(0)
        try:
            result = L('hi').center(10, '=')
            repr_str = repr(result)
            # Should have two concatenations (left + original + right)
            self.assertEqual(repr_str.count('+'), 2)
        finally:
            lstring.set_optimize_threshold(1024)


class TestLStrip(unittest.TestCase):
    """Test L.lstrip() method."""
    
    def test_lstrip_basic(self):
        """Test basic left strip of whitespace."""
        result = L('  hello  ').lstrip()
        self.assertEqual(str(result), 'hello  ')
    
    def test_lstrip_custom_chars(self):
        """Test left strip with custom characters."""
        result = L('---hello---').lstrip('-')
        self.assertEqual(str(result), 'hello---')
    
    def test_lstrip_multiple_chars(self):
        """Test left strip with multiple character types."""
        result = L('.,;hello world').lstrip('.,;')
        self.assertEqual(str(result), 'hello world')
    
    def test_lstrip_nothing_to_strip(self):
        """Test when nothing needs to be stripped."""
        s = L('hello')
        result = s.lstrip()
        self.assertEqual(str(result), 'hello')
        # Should return self when nothing was stripped
        self.assertIs(result, s)
    
    def test_lstrip_lazy_structure(self):
        """Test that lstrip creates lazy slice."""
        import lstring
        lstring.set_optimize_threshold(0)
        try:
            result = L('   hello').lstrip()
            repr_str = repr(result)
            # Should show slice operation
            self.assertIn('[', repr_str)
        finally:
            lstring.set_optimize_threshold(1024)


class TestRStrip(unittest.TestCase):
    """Test L.rstrip() method."""
    
    def test_rstrip_basic(self):
        """Test basic right strip of whitespace."""
        result = L('  hello  ').rstrip()
        self.assertEqual(str(result), '  hello')
    
    def test_rstrip_custom_chars(self):
        """Test right strip with custom characters."""
        result = L('---hello---').rstrip('-')
        self.assertEqual(str(result), '---hello')
    
    def test_rstrip_multiple_chars(self):
        """Test right strip with multiple character types."""
        result = L('hello world.,;').rstrip('.,;')
        self.assertEqual(str(result), 'hello world')
    
    def test_rstrip_nothing_to_strip(self):
        """Test when nothing needs to be stripped."""
        result = L('hello').rstrip()
        self.assertEqual(str(result), 'hello')
    
    def test_rstrip_lazy_structure(self):
        """Test that rstrip creates lazy slice."""
        import lstring
        lstring.set_optimize_threshold(0)
        try:
            result = L('hello   ').rstrip()
            repr_str = repr(result)
            # Should show slice operation
            self.assertIn('[', repr_str)
        finally:
            lstring.set_optimize_threshold(1024)


class TestStrip(unittest.TestCase):
    """Test L.strip() method."""
    
    def test_strip_basic(self):
        """Test basic strip of whitespace from both ends."""
        result = L('  hello  ').strip()
        self.assertEqual(str(result), 'hello')
    
    def test_strip_custom_chars(self):
        """Test strip with custom characters."""
        result = L('---hello---').strip('-')
        self.assertEqual(str(result), 'hello')
    
    def test_strip_asymmetric(self):
        """Test strip with different amounts on each side."""
        result = L(' hello   ').strip()
        self.assertEqual(str(result), 'hello')
    
    def test_strip_multiple_chars(self):
        """Test strip with multiple character types."""
        result = L('.,;hello world.,;').strip('.,;')
        self.assertEqual(str(result), 'hello world')
    
    def test_strip_nothing_to_strip(self):
        """Test when nothing needs to be stripped."""
        result = L('hello').strip()
        self.assertEqual(str(result), 'hello')
    
    def test_strip_lazy_structure(self):
        """Test that strip creates lazy slice."""
        import lstring
        lstring.set_optimize_threshold(0)
        try:
            result = L('  hello  ').strip()
            repr_str = repr(result)
            # Should show slice operation
            self.assertIn('[', repr_str)
        finally:
            lstring.set_optimize_threshold(1024)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error handling."""
    
    def test_ljust_invalid_fillchar(self):
        """Test that ljust raises TypeError for invalid fillchar."""
        with self.assertRaises(TypeError):
            L('hello').ljust(10, 'ab')  # More than one character
        with self.assertRaises(TypeError):
            L('hello').ljust(10, '')  # Empty string
    
    def test_rjust_invalid_fillchar(self):
        """Test that rjust raises TypeError for invalid fillchar."""
        with self.assertRaises(TypeError):
            L('hello').rjust(10, 'ab')
    
    def test_center_invalid_fillchar(self):
        """Test that center raises TypeError for invalid fillchar."""
        with self.assertRaises(TypeError):
            L('hello').center(10, 'ab')
    
    def test_empty_string_operations(self):
        """Test operations on empty strings."""
        empty = L('')
        
        self.assertEqual(str(empty.ljust(5)), '     ')
        self.assertEqual(str(empty.rjust(5)), '     ')
        self.assertEqual(str(empty.center(5)), '     ')
        self.assertEqual(str(empty.lstrip()), '')
        self.assertEqual(str(empty.rstrip()), '')
        self.assertEqual(str(empty.strip()), '')


if __name__ == '__main__':
    unittest.main()
