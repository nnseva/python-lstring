"""
Tests for L.expandtabs() method.
"""

import unittest
from lstring import L


class TestExpandtabs(unittest.TestCase):
    """Test expandtabs method."""
    
    def test_expandtabs_basic(self):
        """Test basic tab expansion with default tabsize."""
        s = L('hello\tworld')
        result = s.expandtabs()
        self.assertEqual(str(result), 'hello   world')
        # 'hello' is 5 chars, next tab stop at 8, so 3 spaces
    
    def test_expandtabs_custom_tabsize(self):
        """Test tab expansion with custom tabsize."""
        s = L('a\tb\tc')
        result = s.expandtabs(4)
        self.assertEqual(str(result), 'a   b   c')
        # Each tab expands to 3 spaces (4 - 1)
    
    def test_expandtabs_multiple_tabs(self):
        """Test multiple consecutive tabs."""
        s = L('\t\t')
        result = s.expandtabs(4)
        self.assertEqual(str(result), '        ')
        # Each tab becomes 4 spaces
    
    def test_expandtabs_at_tabstop(self):
        """Test tab when already at tab stop."""
        s = L('12345678\t')
        result = s.expandtabs(8)
        self.assertEqual(str(result), '12345678        ')
        # At position 8, tab expands to 8 spaces to reach position 16
    
    def test_expandtabs_with_newline(self):
        """Test that newlines reset column position."""
        s = L('hello\tworld\n\tx')
        result = s.expandtabs(8)
        expected = 'hello   world\n        x'
        self.assertEqual(str(result), expected)
    
    def test_expandtabs_with_crlf(self):
        """Test that \\r\\n resets column position."""
        s = L('hello\tworld\r\n\tx')
        result = s.expandtabs(8)
        expected = 'hello   world\r\n        x'
        self.assertEqual(str(result), expected)
    
    def test_expandtabs_with_cr(self):
        """Test that \\r alone resets column position."""
        s = L('hello\tworld\r\tx')
        result = s.expandtabs(8)
        expected = 'hello   world\r        x'
        self.assertEqual(str(result), expected)
    
    def test_expandtabs_empty_string(self):
        """Test expandtabs on empty string."""
        s = L('')
        result = s.expandtabs()
        self.assertEqual(str(result), '')
    
    def test_expandtabs_no_tabs(self):
        """Test expandtabs when no tabs present."""
        s = L('hello world')
        result = s.expandtabs()
        self.assertEqual(str(result), 'hello world')
    
    def test_expandtabs_tabsize_zero(self):
        """Test expandtabs with tabsize=0 removes tabs."""
        s = L('hello\tworld\t!')
        result = s.expandtabs(0)
        self.assertEqual(str(result), 'helloworld!')
    
    def test_expandtabs_tabsize_negative(self):
        """Test expandtabs with negative tabsize removes tabs."""
        s = L('hello\tworld')
        result = s.expandtabs(-1)
        self.assertEqual(str(result), 'helloworld')
    
    def test_expandtabs_tabsize_one(self):
        """Test expandtabs with tabsize=1."""
        s = L('a\tb\tc')
        result = s.expandtabs(1)
        self.assertEqual(str(result), 'a b c')
    
    def test_expandtabs_complex(self):
        """Test complex case with multiple lines and tabs."""
        s = L('Name\tAge\tCity\nAlice\t30\tNY\nBob\t25\tLA')
        result = s.expandtabs(8)
        lines = str(result).split('\n')
        self.assertEqual(lines[0], 'Name    Age     City')
        self.assertEqual(lines[1], 'Alice   30      NY')
        self.assertEqual(lines[2], 'Bob     25      LA')
    
    def test_expandtabs_lazy_structure(self):
        """Test that expandtabs creates lazy structure."""
        s = L('hello\tworld')
        result = s.expandtabs()
        # Should be a join of slices and multiplications
        repr_str = repr(result)
        # Check for lazy structure (slices, multiplication, or join)
        has_lazy = ('[' in repr_str or '*' in repr_str or 'join' in repr_str.lower())
        self.assertTrue(has_lazy, f"Expected lazy structure in {repr_str}")


class TestExpandtabsEdgeCases(unittest.TestCase):
    """Test edge cases for expandtabs."""
    
    def test_only_tabs(self):
        """Test string with only tabs."""
        s = L('\t\t\t')
        result = s.expandtabs(4)
        self.assertEqual(str(result), '            ')  # 3 * 4 = 12 spaces
    
    def test_tab_at_start(self):
        """Test tab at the beginning."""
        s = L('\thello')
        result = s.expandtabs(8)
        self.assertEqual(str(result), '        hello')
    
    def test_tab_at_end(self):
        """Test tab at the end."""
        s = L('hello\t')
        result = s.expandtabs(8)
        self.assertEqual(str(result), 'hello   ')
    
    def test_mixed_newlines(self):
        """Test with mixed newline styles."""
        s = L('a\tb\nc\td\r\ne\tf\rg\th')
        result = s.expandtabs(4)
        expected = 'a   b\nc   d\r\ne   f\rg   h'
        self.assertEqual(str(result), expected)
    
    def test_unicode_before_tab(self):
        """Test unicode characters before tab."""
        s = L('привет\tмир')
        result = s.expandtabs(8)
        # 'привет' is 6 chars, so tab should expand to 2 spaces
        self.assertEqual(str(result), 'привет  мир')
    
    def test_expandtabs_large_tabsize(self):
        """Test with very large tabsize."""
        s = L('a\tb')
        result = s.expandtabs(100)
        # 'a' is 1 char, next tab stop at 100, so 99 spaces
        self.assertEqual(str(result), 'a' + ' ' * 99 + 'b')
    
    def test_comparison_with_str(self):
        """Test that result matches Python's str.expandtabs."""
        test_cases = [
            ('hello\tworld', 8),
            ('a\tb\tc', 4),
            ('\t\t', 8),
            ('hello\tworld\n\tx', 8),
            ('Name\tAge\nAlice\t30', 8),
        ]
        for text, tabsize in test_cases:
            s = L(text)
            result = str(s.expandtabs(tabsize))
            expected = text.expandtabs(tabsize)
            self.assertEqual(result, expected, 
                           f"Failed for text={repr(text)}, tabsize={tabsize}")


if __name__ == '__main__':
    unittest.main()
