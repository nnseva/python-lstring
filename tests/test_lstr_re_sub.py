"""
Unit tests for lstring.re Pattern.sub() and Pattern.subn() methods.
"""

import unittest
import sys
import os

# Add parent directory to path to import lstring
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import lstring
import lstring.re
from lstring import L


class TestPatternSub(unittest.TestCase):
    """Test cases for Pattern.sub() method."""
    
    def test_simple_substitution(self):
        """Test simple string substitution."""
        pattern = lstring.re.compile(r'\d+', compatible=False)
        result = pattern.sub(L('X'), L('foo 123 bar 456'))
        self.assertEqual(str(result), 'foo X bar X')
        self.assertIsInstance(result, type(L('')))
    
    def test_substitution_with_count(self):
        """Test substitution with count limit."""
        pattern = lstring.re.compile(r'\d+', compatible=False)
        result = pattern.sub(L('X'), L('foo 123 bar 456 baz 789'), count=2)
        self.assertEqual(str(result), 'foo X bar X baz 789')
    
    def test_substitution_with_count_one(self):
        """Test substitution with count=1."""
        pattern = lstring.re.compile(r'\d+', compatible=False)
        result = pattern.sub(L('X'), L('foo 123 bar 456'), count=1)
        self.assertEqual(str(result), 'foo X bar 456')
    
    def test_no_matches(self):
        """Test substitution when pattern doesn't match."""
        pattern = lstring.re.compile(r'\d+', compatible=False)
        result = pattern.sub(L('X'), L('foo bar baz'))
        self.assertEqual(str(result), 'foo bar baz')
    
    def test_backreference_substitution(self):
        """Test substitution with backreferences."""
        pattern = lstring.re.compile(r'(\w+):(\d+)', compatible=False)
        result = pattern.sub(r'\2=\1', L('name:100 age:25'))
        self.assertEqual(str(result), '100=name 25=age')
    
    def test_named_group_substitution(self):
        """Test substitution with named groups."""
        pattern = lstring.re.compile(r'(?<key>\w+):(?<value>\d+)', compatible=False)
        result = pattern.sub(r'\g<value>=\g<key>', L('name:100 age:25'))
        self.assertEqual(str(result), '100=name 25=age')
    
    def test_callable_replacement(self):
        """Test substitution with callable replacement."""
        pattern = lstring.re.compile(r'\d+', compatible=False)
        result = pattern.sub(lambda m: L('[' + str(m.group()) + ']'), L('foo 123 bar 456'))
        self.assertEqual(str(result), 'foo [123] bar [456]')
    
    def test_callable_replacement_with_count(self):
        """Test callable replacement with count limit."""
        pattern = lstring.re.compile(r'\d+', compatible=False)
        result = pattern.sub(lambda m: L('[' + str(m.group()) + ']'), L('foo 123 bar 456'), count=1)
        self.assertEqual(str(result), 'foo [123] bar 456')
    
    def test_callable_returning_str(self):
        """Test callable that returns str instead of L."""
        pattern = lstring.re.compile(r'\d+', compatible=False)
        # join() should handle str return values
        result = pattern.sub(lambda m: '[' + str(m.group()) + ']', L('foo 123 bar'))
        self.assertEqual(str(result), 'foo [123] bar')
    
    def test_empty_match_substitution(self):
        """Test substitution with pattern that can match empty string."""
        pattern = lstring.re.compile(r'x*', compatible=False)
        result = pattern.sub(L('-'), L('abc'))
        self.assertEqual(str(result), '-a-b-c-')
    
    def test_empty_match_with_count(self):
        """Test empty match substitution with count limit."""
        pattern = lstring.re.compile(r'x*', compatible=False)
        result = pattern.sub(L('-'), L('abc'), count=2)
        self.assertEqual(str(result), '-a-bc')
    
    def test_substitution_str_input(self):
        """Test substitution with str inputs (should convert to L)."""
        pattern = lstring.re.compile(r'\d+', compatible=False)
        result = pattern.sub('X', 'foo 123 bar 456')
        self.assertEqual(str(result), 'foo X bar X')
        self.assertIsInstance(result, type(L('')))
    
    def test_complex_backreferences(self):
        """Test complex backreference patterns."""
        pattern = lstring.re.compile(r'([a-z]+)(\d+)', compatible=False)
        result = pattern.sub(r'\2\1', L('abc123 def456'))
        self.assertEqual(str(result), '123abc 456def')
    
    def test_escape_sequences_in_replacement(self):
        """Test escape sequences in replacement string."""
        pattern = lstring.re.compile(r'\d+', compatible=False)
        result = pattern.sub(r'X\nY', L('foo 123 bar'))
        self.assertEqual(str(result), 'foo X\nY bar')


class TestPatternSubn(unittest.TestCase):
    """Test cases for Pattern.subn() method."""
    
    def test_simple_substitution_returns_count(self):
        """Test that subn returns (result, count) tuple."""
        pattern = lstring.re.compile(r'\d+', compatible=False)
        result, n = pattern.subn(L('X'), L('foo 123 bar 456'))
        self.assertEqual(str(result), 'foo X bar X')
        self.assertEqual(n, 2)
    
    def test_subn_with_count_limit(self):
        """Test subn with count limit."""
        pattern = lstring.re.compile(r'\d+', compatible=False)
        result, n = pattern.subn(L('X'), L('foo 123 bar 456 baz 789'), count=2)
        self.assertEqual(str(result), 'foo X bar X baz 789')
        self.assertEqual(n, 2)
    
    def test_subn_no_matches(self):
        """Test subn when pattern doesn't match."""
        pattern = lstring.re.compile(r'\d+', compatible=False)
        result, n = pattern.subn(L('X'), L('foo bar baz'))
        self.assertEqual(str(result), 'foo bar baz')
        self.assertEqual(n, 0)
    
    def test_subn_with_backreferences(self):
        """Test subn with backreferences."""
        pattern = lstring.re.compile(r'(\w+):(\d+)', compatible=False)
        result, n = pattern.subn(r'\2=\1', L('name:100 age:25'))
        self.assertEqual(str(result), '100=name 25=age')
        self.assertEqual(n, 2)
    
    def test_subn_callable_replacement(self):
        """Test subn with callable replacement."""
        pattern = lstring.re.compile(r'\d+', compatible=False)
        result, n = pattern.subn(lambda m: L('[' + str(m.group()) + ']'), L('foo 123 bar 456'))
        self.assertEqual(str(result), 'foo [123] bar [456]')
        self.assertEqual(n, 2)
    
    def test_subn_empty_match(self):
        """Test subn with pattern that can match empty string."""
        pattern = lstring.re.compile(r'x*', compatible=False)
        result, n = pattern.subn(L('-'), L('abc'))
        self.assertEqual(str(result), '-a-b-c-')
        self.assertEqual(n, 3)  # Matches before a, b, c
    
    def test_subn_single_match(self):
        """Test subn with single match."""
        pattern = lstring.re.compile(r'bar', compatible=False)
        result, n = pattern.subn(L('BAR'), L('foo bar baz'))
        self.assertEqual(str(result), 'foo BAR baz')
        self.assertEqual(n, 1)


class TestModuleLevelSub(unittest.TestCase):
    """Test cases for module-level sub() and subn() functions."""
    
    def test_sub_module_function(self):
        """Test module-level sub() function."""
        result = lstring.re.sub(r'\d+', L('X'), L('foo 123 bar 456'))
        self.assertEqual(str(result), 'foo X bar X')
    
    def test_sub_with_flags(self):
        """Test module-level sub() with flags."""
        # Skip - flags not yet exported in lstring.re
        self.skipTest("IGNORECASE flag not yet exported")
    
    def test_subn_module_function(self):
        """Test module-level subn() function."""
        result, n = lstring.re.subn(r'\d+', L('X'), L('foo 123 bar 456'))
        self.assertEqual(str(result), 'foo X bar X')
        self.assertEqual(n, 2)
    
    def test_subn_with_flags(self):
        """Test module-level subn() with flags."""
        # Skip - flags not yet exported in lstring.re
        self.skipTest("IGNORECASE flag not yet exported")
    
    def test_sub_with_count(self):
        """Test module-level sub() with count parameter."""
        result = lstring.re.sub(r'\d+', L('X'), L('foo 123 bar 456'), count=1)
        self.assertEqual(str(result), 'foo X bar 456')
    
    def test_subn_with_count(self):
        """Test module-level subn() with count parameter."""
        result, n = lstring.re.subn(r'\d+', L('X'), L('foo 123 bar 456'), count=1)
        self.assertEqual(str(result), 'foo X bar 456')
        self.assertEqual(n, 1)


class TestSubEdgeCases(unittest.TestCase):
    """Test edge cases and special scenarios for sub/subn."""
    
    def test_replacement_at_start(self):
        """Test replacement at the start of string."""
        pattern = lstring.re.compile(r'^\w+', compatible=False)
        result = pattern.sub(L('START'), L('hello world'))
        self.assertEqual(str(result), 'START world')
    
    def test_replacement_at_end(self):
        """Test replacement at the end of string."""
        pattern = lstring.re.compile(r'\w+$', compatible=False)
        result = pattern.sub(L('END'), L('hello world'))
        self.assertEqual(str(result), 'hello END')
    
    def test_full_string_replacement(self):
        """Test replacing entire string."""
        pattern = lstring.re.compile(r'.*', compatible=False)
        result = pattern.sub(L('REPLACED'), L('hello'))
        # Pattern matches 'hello' and then empty string at end
        self.assertEqual(str(result), 'REPLACEDREPLACED')
    
    def test_multiple_groups_in_replacement(self):
        """Test replacement with multiple groups."""
        pattern = lstring.re.compile(r'(\w+)\s+(\w+)\s+(\w+)', compatible=False)
        result = pattern.sub(r'\3 \2 \1', L('one two three'))
        self.assertEqual(str(result), 'three two one')
    
    def test_callable_with_groups(self):
        """Test callable replacement accessing groups."""
        pattern = lstring.re.compile(r'(\d+)', compatible=False)
        result = pattern.sub(
            lambda m: L(str(int(str(m.group(1))) * 2)),
            L('price: 10 quantity: 5')
        )
        self.assertEqual(str(result), 'price: 20 quantity: 10')
    
    def test_empty_replacement(self):
        """Test replacement with empty string (deletion)."""
        pattern = lstring.re.compile(r'\d+', compatible=False)
        result = pattern.sub(L(''), L('foo123bar456baz'))
        self.assertEqual(str(result), 'foobarbaz')
    
    def test_replacement_with_special_chars(self):
        """Test replacement containing special characters."""
        pattern = lstring.re.compile(r'\d+', compatible=False)
        result = pattern.sub(L('$$$'), L('foo 123 bar'))
        self.assertEqual(str(result), 'foo $$$ bar')


if __name__ == '__main__':
    unittest.main()
