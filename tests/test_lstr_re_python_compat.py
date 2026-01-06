"""
Tests for Python re syntax compatibility conversion.
"""

import unittest
import sys
import os
import warnings
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import lstring
import lstring.re
from lstring import L


class TestPythonSyntaxConversion(unittest.TestCase):
    """Test conversion of Python re syntax to Boost regex syntax."""
    
    def test_named_group_conversion(self):
        """Test that (?P<name>...) converts to (?<name>...)."""
        # Use compatible=True (default) to enable conversion
        pattern = lstring.re.compile(r'(?P<word>\w+)', compatible=True)
        match = pattern.match(L('hello'))
        self.assertIsNotNone(match)
        self.assertEqual(str(match.group(L('word'))), 'hello')
    
    def test_named_backref_conversion(self):
        r"""Test that (?P=name) converts to \k<name>."""
        # Pattern with named group and backreference
        pattern = lstring.re.compile(r'(?P<char>\w)\w+(?P=char)', compatible=True)
        
        # Should match words that start and end with same character
        match = pattern.match(L('level'))
        self.assertIsNotNone(match)
        self.assertEqual(str(match.group()), 'level')
        
        # Should not match words with different start/end
        match = pattern.match(L('hello'))
        self.assertIsNone(match)
    
    def test_multiple_named_groups(self):
        """Test pattern with multiple named groups."""
        pattern = lstring.re.compile(
            r'(?P<first>\w+)\s+(?P<second>\w+)',
            compatible=True
        )
        match = pattern.match(L('hello world'))
        self.assertIsNotNone(match)
        self.assertEqual(str(match.group(L('first'))), 'hello')
        self.assertEqual(str(match.group(L('second'))), 'world')
    
    def test_mixed_named_and_numbered_groups(self):
        """Test pattern with both named and numbered groups."""
        pattern = lstring.re.compile(
            r'(?P<name>\w+):(\d+)',
            compatible=True
        )
        match = pattern.match(L('age:25'))
        self.assertIsNotNone(match)
        self.assertEqual(str(match.group(L('name'))), 'age')
        self.assertEqual(str(match.group(1)), 'age')
        self.assertEqual(str(match.group(2)), '25')
    
    def test_nested_named_groups(self):
        """Test nested named groups."""
        pattern = lstring.re.compile(
            r'(?P<outer>(?P<inner>\w+)\s+\w+)',
            compatible=True
        )
        match = pattern.match(L('hello world'))
        self.assertIsNotNone(match)
        self.assertEqual(str(match.group(L('outer'))), 'hello world')
        self.assertEqual(str(match.group(L('inner'))), 'hello')
    
    def test_compatible_false_unchanged(self):
        """Test that compatible=False doesn't convert syntax."""
        # Boost syntax should work directly with compatible=False
        pattern = lstring.re.compile(r'(?<word>\w+)', compatible=False)
        match = pattern.match(L('hello'))
        self.assertIsNotNone(match)
        self.assertEqual(str(match.group(L('word'))), 'hello')
    
    def test_expansion_with_named_groups(self):
        """Test expand() with converted named groups."""
        pattern = lstring.re.compile(
            r'(?P<first>\w+)\s+(?P<second>\w+)',
            compatible=True
        )
        match = pattern.match(L('hello world'))
        result = match.expand(r'\g<second> \g<first>')
        self.assertEqual(str(result), 'world hello')
    
    def test_sub_with_named_groups(self):
        """Test sub() with converted named groups."""
        pattern = lstring.re.compile(
            r'(?P<word>\w+)',
            compatible=True
        )
        result = pattern.sub(r'[\g<word>]', L('hello world'))
        self.assertEqual(str(result), '[hello] [world]')
    
    def test_complex_pattern_with_backrefs(self):
        """Test complex pattern with multiple backreferences."""
        # Match repeated words like "hello hello"
        pattern = lstring.re.compile(
            r'(?P<word>\w+)\s+(?P=word)',
            compatible=True
        )
        
        match = pattern.match(L('test test'))
        self.assertIsNotNone(match)
        
        match = pattern.match(L('test other'))
        self.assertIsNone(match)


class TestConversionEdgeCases(unittest.TestCase):
    """Test edge cases in Python syntax conversion."""
    
    def test_empty_named_group_name(self):
        """Test that pattern compiles even with unusual group names."""
        # Single character group name
        pattern = lstring.re.compile(r'(?P<a>\w+)', compatible=True)
        match = pattern.match(L('test'))
        self.assertIsNotNone(match)
        self.assertEqual(str(match.group(L('a'))), 'test')
    
    def test_underscore_in_group_name(self):
        """Test group names with underscores."""
        pattern = lstring.re.compile(r'(?P<first_name>\w+)', compatible=True)
        match = pattern.match(L('John'))
        self.assertIsNotNone(match)
        self.assertEqual(str(match.group(L('first_name'))), 'John')
    
    def test_digits_in_group_name(self):
        """Test group names with digits."""
        pattern = lstring.re.compile(r'(?P<group1>\w+)', compatible=True)
        match = pattern.match(L('test'))
        self.assertIsNotNone(match)
        self.assertEqual(str(match.group(L('group1'))), 'test')
    
    def test_pattern_without_python_syntax(self):
        """Test that patterns without Python syntax work unchanged."""
        pattern = lstring.re.compile(r'\d+', compatible=True)
        match = pattern.match(L('123'))
        self.assertIsNotNone(match)
        self.assertEqual(str(match.group()), '123')
    
    def test_literal_question_mark(self):
        r"""Test that literal \? doesn't interfere with conversion."""
        pattern = lstring.re.compile(r'test\?', compatible=True)
        match = pattern.match(L('test?'))
        self.assertIsNotNone(match)


class TestConvertPythonToBoost(unittest.TestCase):
    """Test the _convert_python_to_boost static method directly."""
    
    def test_simple_named_group(self):
        """Test conversion of a simple named group."""
        input_pattern = L('(?P<name>\\w+)')
        result = lstring.re.Pattern._convert_python_to_boost(input_pattern)
        self.assertEqual(str(result), '(?<name>\\w+)')
    
    def test_simple_named_backref(self):
        """Test conversion of a simple named backreference."""
        input_pattern = L('(?P=name)')
        result = lstring.re.Pattern._convert_python_to_boost(input_pattern)
        self.assertEqual(str(result), '\\k<name>')
    
    def test_multiple_named_groups(self):
        """Test conversion of multiple named groups."""
        input_pattern = L('(?P<first>\\w+)\\s+(?P<second>\\w+)')
        result = lstring.re.Pattern._convert_python_to_boost(input_pattern)
        self.assertEqual(str(result), '(?<first>\\w+)\\s+(?<second>\\w+)')
    
    def test_named_group_with_backref(self):
        """Test conversion of named group with its backreference."""
        input_pattern = L('(?P<char>\\w)\\w+(?P=char)')
        result = lstring.re.Pattern._convert_python_to_boost(input_pattern)
        self.assertEqual(str(result), '(?<char>\\w)\\w+\\k<char>')
    
    def test_nested_groups(self):
        """Test conversion with nested groups."""
        input_pattern = L('(?P<outer>(?P<inner>\\w+))')
        result = lstring.re.Pattern._convert_python_to_boost(input_pattern)
        self.assertEqual(str(result), '(?<outer>(?<inner>\\w+))')
    
    def test_pattern_without_python_syntax(self):
        """Test that pattern without Python syntax remains unchanged."""
        input_pattern = L('\\d+\\w+')
        result = lstring.re.Pattern._convert_python_to_boost(input_pattern)
        self.assertEqual(str(result), '\\d+\\w+')
    
    def test_partial_prefix_not_converted(self):
        """Test that partial prefix (?P without < or = is not converted."""
        input_pattern = L('(?P)')
        result = lstring.re.Pattern._convert_python_to_boost(input_pattern)
        self.assertEqual(str(result), '(?P)')
    
    def test_prefix_at_end_not_converted(self):
        """Test that (?P at end of pattern is copied as-is."""
        input_pattern = L('test(?P')
        result = lstring.re.Pattern._convert_python_to_boost(input_pattern)
        self.assertEqual(str(result), 'test(?P')
    
    def test_mixed_content(self):
        """Test pattern with Python syntax mixed with regular content."""
        input_pattern = L('start(?P<name>\\w+)middle(?P=name)end')
        result = lstring.re.Pattern._convert_python_to_boost(input_pattern)
        self.assertEqual(str(result), 'start(?<name>\\w+)middle\\k<name>end')
    
    def test_consecutive_named_groups(self):
        """Test consecutive named groups."""
        input_pattern = L('(?P<a>x)(?P<b>y)(?P<c>z)')
        result = lstring.re.Pattern._convert_python_to_boost(input_pattern)
        self.assertEqual(str(result), '(?<a>x)(?<b>y)(?<c>z)')
    
    def test_empty_pattern(self):
        """Test conversion of empty pattern."""
        input_pattern = L('')
        result = lstring.re.Pattern._convert_python_to_boost(input_pattern)
        self.assertEqual(str(result), '')
    
    def test_backref_with_digits_in_name(self):
        """Test named backreference with digits in name."""
        input_pattern = L('(?P<name123>\\w+)(?P=name123)')
        result = lstring.re.Pattern._convert_python_to_boost(input_pattern)
        self.assertEqual(str(result), '(?<name123>\\w+)\\k<name123>')
    
    def test_backref_with_underscores(self):
        """Test named backreference with underscores."""
        input_pattern = L('(?P<my_name>\\w+)(?P=my_name)')
        result = lstring.re.Pattern._convert_python_to_boost(input_pattern)
        self.assertEqual(str(result), '(?<my_name>\\w+)\\k<my_name>')
    
    def test_prefix_without_closing_paren(self):
        """Test (?P= without closing parenthesis."""
        input_pattern = L('(?P=name')
        result = lstring.re.Pattern._convert_python_to_boost(input_pattern)
        # Should copy as-is since no closing )
        self.assertEqual(str(result), '(?P=name')
    
    def test_multiple_backrefs(self):
        """Test multiple backreferences to the same group."""
        input_pattern = L('(?P<x>\\w)(?P=x)(?P=x)')
        result = lstring.re.Pattern._convert_python_to_boost(input_pattern)
        self.assertEqual(str(result), '(?<x>\\w)\\k<x>\\k<x>')

    def test_inline_unsupported_flags_stripped_with_warnings(self):
        """(?a) and (?L) are stripped with warnings; (?u) is stripped silently."""
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always')

            r1 = lstring.re.Pattern._convert_python_to_boost(L('(?a)abc'))
            r2 = lstring.re.Pattern._convert_python_to_boost(L('(?L)abc'))
            r3 = lstring.re.Pattern._convert_python_to_boost(L('(?u)abc'))

        self.assertEqual(str(r1), 'abc')
        self.assertEqual(str(r2), 'abc')
        self.assertEqual(str(r3), 'abc')

        messages = [str(w.message) for w in caught]
        self.assertTrue(any('(?a)' in msg for msg in messages), messages)
        self.assertTrue(any('(?L)' in msg for msg in messages), messages)
        self.assertFalse(any('(?u)' in msg for msg in messages), messages)

    def test_inline_unsupported_flags_preserve_other_flags(self):
        """Unsupported flags are removed without dropping supported inline flags."""
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always')
            result = lstring.re.Pattern._convert_python_to_boost(L('(?ai)abc'))

        self.assertEqual(str(result), '(?i)abc')
        self.assertTrue(any('(?a)' in str(w.message) for w in caught), [str(w.message) for w in caught])

    def test_inline_unsupported_scoped_group_becomes_noncapturing(self):
        """(?a:...) with only unsupported flags becomes (?:...)."""
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always')
            result = lstring.re.Pattern._convert_python_to_boost(L('(?a:ab)c'))

        self.assertEqual(str(result), '(?:ab)c')
        self.assertTrue(any('(?a)' in str(w.message) for w in caught), [str(w.message) for w in caught])


class TestPatternConstruction(unittest.TestCase):
    """Test that _convert_python_to_boost is called correctly during Pattern construction."""
    
    def test_compatible_true_calls_conversion(self):
        """Test that compatible=True triggers conversion."""
        with patch.object(lstring.re.Pattern, '_convert_python_to_boost', 
                         wraps=lstring.re.Pattern._convert_python_to_boost) as mock_convert:
            pattern = lstring.re.Pattern(L('(?P<name>\\w+)'), compatible=True)
            mock_convert.assert_called_once()
            # Verify the argument passed to conversion
            call_args = mock_convert.call_args[0][0]
            self.assertEqual(str(call_args), '(?P<name>\\w+)')
    
    def test_compatible_false_skips_conversion(self):
        """Test that compatible=False skips conversion."""
        with patch.object(lstring.re.Pattern, '_convert_python_to_boost') as mock_convert:
            pattern = lstring.re.Pattern(L('(?<name>\\w+)'), compatible=False)
            mock_convert.assert_not_called()
    
    def test_compile_function_passes_compatible(self):
        """Test that compile function passes compatible parameter correctly."""
        with patch.object(lstring.re.Pattern, '_convert_python_to_boost',
                         wraps=lstring.re.Pattern._convert_python_to_boost) as mock_convert:
            # compatible=True (default)
            pattern1 = lstring.re.compile(L('(?P<name>\\w+)'))
            self.assertEqual(mock_convert.call_count, 1)
            
            # compatible=False
            pattern2 = lstring.re.compile(L('(?<name>\\w+)'), compatible=False)
            # Still 1 because compatible=False doesn't call it
            self.assertEqual(mock_convert.call_count, 1)
    
    def test_str_pattern_converted_to_L(self):
        """Test that str pattern is converted to L before conversion."""
        with patch.object(lstring.re.Pattern, '_convert_python_to_boost',
                         wraps=lstring.re.Pattern._convert_python_to_boost) as mock_convert:
            # Pass str instead of L
            pattern = lstring.re.Pattern('(?P<name>\\w+)', compatible=True)
            mock_convert.assert_called_once()
            # Verify the argument is L type
            call_args = mock_convert.call_args[0][0]
            self.assertIsInstance(call_args, type(L('')))


class TestPatternConstructorInlineUnsupportedFlags(unittest.TestCase):
    def test_constructor_inline_a_warns_and_compiles(self):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always', RuntimeWarning)
            pat = lstring.re.Pattern(L('(?a)abc'), compatible=True)

        self.assertIsNotNone(pat.fullmatch(L('abc')))
        self.assertTrue(any('(?a)' in str(w.message) for w in caught), [str(w.message) for w in caught])

    def test_constructor_inline_L_warns_and_compiles(self):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always', RuntimeWarning)
            pat = lstring.re.Pattern(L('(?L)abc'), compatible=True)

        self.assertIsNotNone(pat.fullmatch(L('abc')))
        self.assertTrue(any('(?L)' in str(w.message) for w in caught), [str(w.message) for w in caught])

    def test_constructor_inline_u_silent_and_compiles(self):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always', RuntimeWarning)
            pat = lstring.re.Pattern(L('(?u)abc'), compatible=True)

        self.assertIsNotNone(pat.fullmatch(L('abc')))
        self.assertEqual([str(w.message) for w in caught], [])

    def test_constructor_inline_ai_preserves_i(self):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always', RuntimeWarning)
            pat = lstring.re.Pattern(L('(?ai)abc'), compatible=True)

        self.assertIsNotNone(pat.fullmatch(L('ABC')))
        self.assertTrue(any('(?a)' in str(w.message) for w in caught), [str(w.message) for w in caught])

    def test_constructor_inline_scoped_a_becomes_noncapturing(self):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always', RuntimeWarning)
            pat = lstring.re.Pattern(L('(?a:ab)c'), compatible=True)

        self.assertIsNotNone(pat.fullmatch(L('abc')))
        self.assertTrue(any('(?a)' in str(w.message) for w in caught), [str(w.message) for w in caught])


if __name__ == '__main__':
    unittest.main()

