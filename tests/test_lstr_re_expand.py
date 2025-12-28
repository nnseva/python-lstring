"""Tests for Match.expand() method."""

import unittest
import lstring
import lstring.re


class TestMatchExpand(unittest.TestCase):
    """Test Match.expand() method with various templates."""
    
    def test_simple_numeric_backreferences(self):
        """Test basic \1, \2, etc. backreferences."""
        pattern = lstring.re.compile(r'(\w+) (\w+)')
        match = pattern.match('hello world')
        
        self.assertEqual(str(match.expand(r'\1')), 'hello')
        self.assertEqual(str(match.expand(r'\2')), 'world')
        self.assertEqual(str(match.expand(r'\1 \2')), 'hello world')
        self.assertEqual(str(match.expand(r'\2 \1')), 'world hello')
    
    def test_group_zero(self):
        """Test \0 and \g<0> for entire match."""
        pattern = lstring.re.compile(r'(\w+) (\w+)')
        match = pattern.match('hello world')
        
        self.assertEqual(str(match.expand(r'\0')), 'hello world')
        self.assertEqual(str(match.expand(r'\g<0>')), 'hello world')
    
    def test_two_digit_backreferences(self):
        """Test two-digit group numbers \10, \11, etc."""
        # Create pattern with 10+ groups
        pattern = lstring.re.compile(r'(\w)(\w)(\w)(\w)(\w)(\w)(\w)(\w)(\w)(\w)(\w)')
        match = pattern.match('abcdefghijk')
        
        self.assertEqual(str(match.expand(r'\10')), 'j')  # 10th group
        self.assertEqual(str(match.expand(r'\11')), 'k')  # 11th group
        self.assertEqual(str(match.expand(r'\1\2')), 'ab')  # 1st and 2nd
    
    def test_named_groups(self):
        """Test \g<name> for named groups."""
        pattern = lstring.re.compile(r'(?<first>\w+) (?<second>\w+)')
        match = pattern.match('hello world')
        
        self.assertEqual(str(match.expand(r'\g<first>')), 'hello')
        self.assertEqual(str(match.expand(r'\g<second>')), 'world')
        self.assertEqual(str(match.expand(r'\g<second> \g<first>')), 'world hello')
    
    def test_numbered_groups_with_angle_brackets(self):
        """Test \g<1>, \g<2> syntax."""
        pattern = lstring.re.compile(r'(\w+) (\w+)')
        match = pattern.match('hello world')
        
        self.assertEqual(str(match.expand(r'\g<1>')), 'hello')
        self.assertEqual(str(match.expand(r'\g<2>')), 'world')
    
    def test_escape_sequences(self):
        """Test escape sequences like \\n, \\t, \\\\, etc."""
        pattern = lstring.re.compile(r'(\w+)')
        match = pattern.match('test')
        
        self.assertEqual(str(match.expand(r'\1\n')), 'test\n')
        self.assertEqual(str(match.expand(r'\1\t')), 'test\t')
        self.assertEqual(str(match.expand(r'\1\\')), 'test\\')
        self.assertEqual(str(match.expand(r'\1\r')), 'test\r')
        self.assertEqual(str(match.expand(r'\1\a')), 'test\a')
        self.assertEqual(str(match.expand(r'\1\b')), 'test\b')
        self.assertEqual(str(match.expand(r'\1\f')), 'test\f')
        self.assertEqual(str(match.expand(r'\1\v')), 'test\v')
    
    def test_literal_text(self):
        """Test that literal text is preserved."""
        pattern = lstring.re.compile(r'(\w+)')
        match = pattern.match('test')
        
        self.assertEqual(str(match.expand(r'prefix-\1-suffix')), 'prefix-test-suffix')
        self.assertEqual(str(match.expand(r'just literal text')), 'just literal text')
    
    def test_optional_groups_not_matched(self):
        """Test groups that didn't match (should be replaced with empty string)."""
        pattern = lstring.re.compile(r'(\w+)(\s+)?(\w+)?')
        match = pattern.match('hello')
        
        # Group 1 matched, groups 2 and 3 didn't
        self.assertEqual(str(match.expand(r'\1')), 'hello')
        self.assertEqual(str(match.expand(r'\1\2\3')), 'hello')  # \2 and \3 are empty
        self.assertEqual(str(match.expand(r'\1-\2-\3')), 'hello--')  # Dashes remain
    
    def test_bad_escape_error(self):
        """Test that bad escape sequences raise ValueError."""
        pattern = lstring.re.compile(r'(\w+)')
        match = pattern.match('test')
        
        with self.assertRaises(ValueError) as cm:
            match.expand(r'\1\x')
        self.assertIn('bad escape', str(cm.exception))
    
    def test_unterminated_group_reference(self):
        """Test that unterminated \g< raises ValueError."""
        pattern = lstring.re.compile(r'(\w+)')
        match = pattern.match('test')
        
        with self.assertRaises(ValueError) as cm:
            match.expand(r'\g<incomplete')
        self.assertIn('missing >', str(cm.exception))
    
    def test_trailing_backslash(self):
        """Test that trailing backslash raises ValueError."""
        pattern = lstring.re.compile(r'(\w+)')
        match = pattern.match('test')
        
        with self.assertRaises(ValueError) as cm:
            match.expand('\\1\\')
        self.assertIn('bad escape', str(cm.exception))
    
    def test_with_lstring_L_template(self):
        """Test that expand() works with lstring.L templates."""
        from lstring import L
        
        pattern = lstring.re.compile(r'(\w+) (\w+)')
        match = pattern.match('hello world')
        
        # Pass L() instead of str
        result = match.expand(L(r'\2 \1'))
        self.assertEqual(str(result), 'world hello')
    
    def test_complex_template(self):
        """Test a complex template with multiple features."""
        pattern = lstring.re.compile(r'(?<name>\w+)@(?<domain>\w+)\.(?<tld>\w+)')
        match = pattern.match('user@example.com')
        
        template = r'Email: \g<name> at \g<domain> dot \g<tld>\nFull: \0'
        result = match.expand(template)
        
        expected = 'Email: user at example dot com\nFull: user@example.com'
        self.assertEqual(str(result), expected)
    
    def test_empty_template(self):
        """Test expand with empty template."""
        pattern = lstring.re.compile(r'(\w+)')
        match = pattern.match('test')
        
        result = match.expand('')
        self.assertEqual(str(result), '')
    
    def test_no_groups_template(self):
        """Test template with no backreferences."""
        pattern = lstring.re.compile(r'(\w+)')
        match = pattern.match('test')
        
        result = match.expand('literal')
        self.assertEqual(str(result), 'literal')


if __name__ == '__main__':
    unittest.main()
