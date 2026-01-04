"""
Tests for L.splitlines method
"""

import unittest
from lstring import L


class TestLStrSplitlines(unittest.TestCase):
    """Tests for L.splitlines method"""
    
    def test_splitlines_basic_lf(self):
        """Test basic splitlines with LF (\\n)"""
        s = L('hello\nworld\ntest')
        result = s.splitlines()
        self.assertEqual(result, [L('hello'), L('world'), L('test')])
    
    def test_splitlines_basic_crlf(self):
        """Test basic splitlines with CRLF (\\r\\n)"""
        s = L('hello\r\nworld\r\ntest')
        result = s.splitlines()
        self.assertEqual(result, [L('hello'), L('world'), L('test')])
    
    def test_splitlines_basic_cr(self):
        """Test basic splitlines with CR (\\r)"""
        s = L('hello\rworld\rtest')
        result = s.splitlines()
        self.assertEqual(result, [L('hello'), L('world'), L('test')])
    
    def test_splitlines_mixed_line_breaks(self):
        """Test splitlines with mixed line break types"""
        s = L('line1\nline2\r\nline3\rline4')
        result = s.splitlines()
        self.assertEqual(result, [L('line1'), L('line2'), L('line3'), L('line4')])
    
    def test_splitlines_keepends_false(self):
        """Test splitlines with keepends=False (default)"""
        s = L('hello\nworld\n')
        result = s.splitlines(keepends=False)
        self.assertEqual(result, [L('hello'), L('world')])
    
    def test_splitlines_keepends_true(self):
        """Test splitlines with keepends=True"""
        s = L('hello\nworld\n')
        result = s.splitlines(keepends=True)
        self.assertEqual(result, [L('hello\n'), L('world\n')])
    
    def test_splitlines_keepends_crlf(self):
        """Test splitlines with keepends=True and CRLF"""
        s = L('hello\r\nworld\r\n')
        result = s.splitlines(keepends=True)
        self.assertEqual(result, [L('hello\r\n'), L('world\r\n')])
    
    def test_splitlines_empty_string(self):
        """Test splitlines on empty string"""
        s = L('')
        result = s.splitlines()
        self.assertEqual(result, [])
    
    def test_splitlines_no_line_breaks(self):
        """Test splitlines on string without line breaks"""
        s = L('hello world')
        result = s.splitlines()
        self.assertEqual(result, [L('hello world')])
    
    def test_splitlines_only_line_breaks(self):
        """Test splitlines on string with only line breaks"""
        s = L('\n\n\n')
        result = s.splitlines()
        self.assertEqual(result, [L(''), L(''), L('')])
    
    def test_splitlines_trailing_newline(self):
        """Test splitlines with trailing newline"""
        s = L('hello\nworld\n')
        result = s.splitlines()
        self.assertEqual(result, [L('hello'), L('world')])
    
    def test_splitlines_leading_newline(self):
        """Test splitlines with leading newline"""
        s = L('\nhello\nworld')
        result = s.splitlines()
        self.assertEqual(result, [L(''), L('hello'), L('world')])
    
    def test_splitlines_empty_lines(self):
        """Test splitlines with empty lines"""
        s = L('hello\n\nworld')
        result = s.splitlines()
        self.assertEqual(result, [L('hello'), L(''), L('world')])
    
    def test_splitlines_vertical_tab(self):
        """Test splitlines with vertical tab (\\v)"""
        s = L('hello\vworld')
        result = s.splitlines()
        self.assertEqual(result, [L('hello'), L('world')])
    
    def test_splitlines_form_feed(self):
        """Test splitlines with form feed (\\f)"""
        s = L('hello\fworld')
        result = s.splitlines()
        self.assertEqual(result, [L('hello'), L('world')])
    
    def test_splitlines_file_separator(self):
        """Test splitlines with file separator (\\x1c)"""
        s = L('hello\x1cworld')
        result = s.splitlines()
        self.assertEqual(result, [L('hello'), L('world')])
    
    def test_splitlines_group_separator(self):
        """Test splitlines with group separator (\\x1d)"""
        s = L('hello\x1dworld')
        result = s.splitlines()
        self.assertEqual(result, [L('hello'), L('world')])
    
    def test_splitlines_record_separator(self):
        """Test splitlines with record separator (\\x1e)"""
        s = L('hello\x1eworld')
        result = s.splitlines()
        self.assertEqual(result, [L('hello'), L('world')])
    
    def test_splitlines_unicode_line_separator(self):
        """Test splitlines with Unicode line separator (\\u2028)"""
        s = L('hello\u2028world')
        result = s.splitlines()
        self.assertEqual(result, [L('hello'), L('world')])
    
    def test_splitlines_unicode_paragraph_separator(self):
        """Test splitlines with Unicode paragraph separator (\\u2029)"""
        s = L('hello\u2029world')
        result = s.splitlines()
        self.assertEqual(result, [L('hello'), L('world')])
    
    def test_splitlines_mixed_keepends(self):
        """Test splitlines with mixed line breaks and keepends=True"""
        s = L('line1\nline2\r\nline3\r')
        result = s.splitlines(keepends=True)
        self.assertEqual(result, [L('line1\n'), L('line2\r\n'), L('line3\r')])
    
    def test_splitlines_compare_with_str(self):
        """Compare L.splitlines() with str.splitlines()"""
        test_strings = [
            'hello\nworld',
            'hello\r\nworld',
            'hello\rworld',
            'line1\nline2\r\nline3',
            '\n\n\n',
            'hello\n',
            '\nhello',
            'hello\n\nworld',
            'no line breaks',
            '',
        ]
        
        for s in test_strings:
            l_result = L(s).splitlines()
            str_result = s.splitlines()
            # Convert str results to L for comparison
            expected = [L(line) for line in str_result]
            self.assertEqual(l_result, expected, f"Failed for: {repr(s)}")
            
            # Test with keepends=True
            l_result_keep = L(s).splitlines(keepends=True)
            str_result_keep = s.splitlines(keepends=True)
            expected_keep = [L(line) for line in str_result_keep]
            self.assertEqual(l_result_keep, expected_keep, f"Failed with keepends for: {repr(s)}")


if __name__ == '__main__':
    unittest.main()
