"""
Comprehensive unit tests for L.findcr() and L.rfindcr() methods.

Tests cover:
- Integer code point parameters
- Single-character string parameters
- Mixed parameter types
- start/end slice parameters
- invert parameter
- Error handling and validation
- Edge cases
"""

import unittest
from lstring import L


class TestFindcr(unittest.TestCase):
    """Test L.findcr() method with various parameter combinations."""

    def test_basic_int_params(self):
        """Test findcr with integer code point parameters."""
        s = L('Hello WORLD 123')
        # Find uppercase letter (A-Z is 65-91)
        self.assertEqual(s.findcr(65, 91), 0)  # 'H' at index 0
        # Find digit (0-9 is 48-58)
        self.assertEqual(s.findcr(48, 58), 12)  # '1' at index 12

    def test_basic_char_params(self):
        """Test findcr with single-character string parameters."""
        s = L('Hello WORLD 123')
        # Find uppercase letter using characters
        self.assertEqual(s.findcr('A', '['), 0)  # 'H' at index 0
        # Find digit using characters
        self.assertEqual(s.findcr('0', ':'), 12)  # '1' at index 12

    def test_mixed_params(self):
        """Test findcr with mixed int and string parameters."""
        s = L('abc123XYZ')
        # Mix: int start, char end
        self.assertEqual(s.findcr(48, ':'), 3)  # '1' at index 3
        # Mix: char start, int end
        self.assertEqual(s.findcr('X', 91), 6)  # 'X' at index 6

    def test_equivalence_int_char(self):
        """Test that int and char parameters produce same results."""
        s = L('Test String 42')
        # A-Z range
        self.assertEqual(s.findcr('A', '['), s.findcr(65, 91))
        # 0-9 range
        self.assertEqual(s.findcr('0', ':'), s.findcr(48, 58))

    def test_with_start_param(self):
        """Test findcr with start parameter."""
        s = L('abc123xyz456')
        # Find first digit
        self.assertEqual(s.findcr(48, 58), 3)
        # Find first digit after index 6
        self.assertEqual(s.findcr(48, 58, 6), 9)
        # Negative start
        self.assertEqual(s.findcr(48, 58, -6), 9)

    def test_with_end_param(self):
        """Test findcr with end parameter."""
        s = L('abc123xyz456')
        # Find digit in first 6 characters
        self.assertEqual(s.findcr(48, 58, 0, 6), 3)
        # Find digit in range that excludes all digits
        self.assertEqual(s.findcr(48, 58, 0, 3), -1)
        # Negative end: -3 means len-3 = 12-3 = 9, so search in [0:9)
        self.assertEqual(s.findcr(48, 58, 0, -3), 3)

    def test_with_start_and_end(self):
        """Test findcr with both start and end parameters."""
        s = L('abc123xyz456')
        # Find digit in middle section
        self.assertEqual(s.findcr(48, 58, 3, 6), 3)
        # No digit in letter-only section
        self.assertEqual(s.findcr(48, 58, 6, 9), -1)

    def test_invert_false(self):
        """Test findcr with invert=False (default behavior)."""
        s = L('ABC123')
        # Find character IN range
        self.assertEqual(s.findcr(65, 91, invert=False), 0)  # 'A'
        self.assertEqual(s.findcr(48, 58, invert=False), 3)  # '1'

    def test_invert_true(self):
        """Test findcr with invert=True (find NOT in range)."""
        s = L('ABC123')
        # Find character NOT in A-Z range
        self.assertEqual(s.findcr(65, 91, invert=True), 3)  # '1'
        # Find character NOT in 0-9 range
        self.assertEqual(s.findcr(48, 58, invert=True), 0)  # 'A'

    def test_not_found(self):
        """Test findcr when no matching character exists."""
        s = L('abcdef')
        # No digits in string
        self.assertEqual(s.findcr(48, 58), -1)
        # No uppercase in string
        self.assertEqual(s.findcr(65, 91), -1)

    def test_empty_string(self):
        """Test findcr on empty string."""
        s = L('')
        self.assertEqual(s.findcr(65, 91), -1)
        self.assertEqual(s.findcr('A', 'Z'), -1)

    def test_single_char_string(self):
        """Test findcr on single character string."""
        s = L('A')
        self.assertEqual(s.findcr(65, 91), 0)  # Found
        self.assertEqual(s.findcr(48, 58), -1)  # Not found

    def test_unicode_ranges(self):
        """Test findcr with Unicode character ranges."""
        # Cyrillic: А-Я is 1040-1072, а-я is 1072-1104
        s = L('Привет')
        # Find uppercase Cyrillic
        self.assertEqual(s.findcr(1040, 1072), 0)  # 'П'
        # Find lowercase Cyrillic
        self.assertEqual(s.findcr(1072, 1104), 1)  # 'р'

    def test_boundary_conditions(self):
        """Test findcr at string boundaries."""
        s = L('ABC')
        # Match at start
        self.assertEqual(s.findcr(65, 91, 0), 0)
        # Match at end
        self.assertEqual(s.findcr(65, 91, 2), 2)
        # Start beyond string
        self.assertEqual(s.findcr(65, 91, 10), -1)
        # End at 0
        self.assertEqual(s.findcr(65, 91, 0, 0), -1)

    def test_slice_clamping(self):
        """Test that start/end are clamped to valid range."""
        s = L('ABC123')
        # Negative start clamped to 0
        self.assertEqual(s.findcr(65, 91, -100), 0)
        # End beyond length clamped to length
        self.assertEqual(s.findcr(65, 91, 0, 100), 0)

    def test_error_startcp_not_int_or_str(self):
        """Test error when startcp is neither int nor string."""
        s = L('test')
        with self.assertRaises(TypeError) as cm:
            s.findcr([65], 91)
        self.assertIn('startcp must be int or 1-char str', str(cm.exception))

    def test_error_endcp_not_int_or_str(self):
        """Test error when endcp is neither int nor string."""
        s = L('test')
        with self.assertRaises(TypeError) as cm:
            s.findcr(65, [91])
        self.assertIn('endcp must be int or 1-char str', str(cm.exception))

    def test_error_multichar_startcp(self):
        """Test error when startcp is multi-character string."""
        s = L('test')
        with self.assertRaises(ValueError) as cm:
            s.findcr('AB', 'Z')
        self.assertIn('startcp must be an int or single character string', str(cm.exception))

    def test_error_multichar_endcp(self):
        """Test error when endcp is multi-character string."""
        s = L('test')
        with self.assertRaises(ValueError) as cm:
            s.findcr('A', 'XYZ')
        self.assertIn('endcp must be an int or single character string', str(cm.exception))

    def test_error_negative_startcp(self):
        """Test error when startcp is negative."""
        s = L('test')
        with self.assertRaises(ValueError) as cm:
            s.findcr(-1, 100)
        self.assertIn('startcp must be a non-negative code point', str(cm.exception))

    def test_error_negative_endcp(self):
        """Test error when endcp is negative."""
        s = L('test')
        with self.assertRaises(ValueError) as cm:
            s.findcr(0, -1)
        self.assertIn('endcp must be a non-negative code point', str(cm.exception))

    def test_error_startcp_gte_endcp(self):
        """Test error when startcp >= endcp."""
        s = L('test')
        # Equal
        with self.assertRaises(ValueError) as cm:
            s.findcr(65, 65)
        self.assertIn('startcp must be less than endcp', str(cm.exception))
        # Greater
        with self.assertRaises(ValueError) as cm:
            s.findcr(91, 65)
        self.assertIn('startcp must be less than endcp', str(cm.exception))

    def test_error_startcp_gte_endcp_chars(self):
        """Test error when startcp >= endcp with character params."""
        s = L('test')
        # 'Z' (90) > '[' (91) is false, but '[' (91) < 'A' (65) is true
        with self.assertRaises(ValueError) as cm:
            s.findcr('[', 'A')  # 91 >= 65
        self.assertIn('startcp must be less than endcp', str(cm.exception))

    def test_error_invalid_start_type(self):
        """Test error when start parameter has wrong type."""
        s = L('test')
        with self.assertRaises(TypeError) as cm:
            s.findcr(65, 91, 'invalid')
        self.assertIn('start must be int or None', str(cm.exception))

    def test_error_invalid_end_type(self):
        """Test error when end parameter has wrong type."""
        s = L('test')
        with self.assertRaises(TypeError) as cm:
            s.findcr(65, 91, 0, 'invalid')
        self.assertIn('end must be int or None', str(cm.exception))


class TestRfindcr(unittest.TestCase):
    """Test L.rfindcr() method with various parameter combinations."""

    def test_basic_int_params(self):
        """Test rfindcr with integer code point parameters."""
        s = L('Hello WORLD 123')
        # Find last uppercase letter (A-Z is 65-91)
        self.assertEqual(s.rfindcr(65, 91), 10)  # 'D' at index 10
        # Find last digit (0-9 is 48-58)
        self.assertEqual(s.rfindcr(48, 58), 14)  # '3' at index 14

    def test_basic_char_params(self):
        """Test rfindcr with single-character string parameters."""
        s = L('Hello WORLD 123')
        # Find last uppercase letter using characters
        self.assertEqual(s.rfindcr('A', '['), 10)  # 'D' at index 10
        # Find last digit using characters
        self.assertEqual(s.rfindcr('0', ':'), 14)  # '3' at index 14

    def test_mixed_params(self):
        """Test rfindcr with mixed int and string parameters."""
        s = L('abc123XYZ')
        # Mix: int start, char end
        self.assertEqual(s.rfindcr(48, ':'), 5)  # '3' at index 5
        # Mix: char start, int end
        self.assertEqual(s.rfindcr('X', 91), 8)  # 'Z' at index 8

    def test_equivalence_int_char(self):
        """Test that int and char parameters produce same results."""
        s = L('Test String 42')
        # A-Z range
        self.assertEqual(s.rfindcr('A', '['), s.rfindcr(65, 91))
        # 0-9 range
        self.assertEqual(s.rfindcr('0', ':'), s.rfindcr(48, 58))

    def test_with_start_param(self):
        """Test rfindcr with start parameter."""
        s = L('abc123xyz456')
        # Find last digit
        self.assertEqual(s.rfindcr(48, 58), 11)
        # Find last digit starting from index 6
        self.assertEqual(s.rfindcr(48, 58, 6), 11)
        # Exclude early digits
        self.assertEqual(s.rfindcr(48, 58, 9), 11)

    def test_with_end_param(self):
        """Test rfindcr with end parameter."""
        s = L('abc123xyz456')
        # Find last digit before index 9
        self.assertEqual(s.rfindcr(48, 58, 0, 9), 5)
        # Find last digit before index 6
        self.assertEqual(s.rfindcr(48, 58, 0, 6), 5)

    def test_with_start_and_end(self):
        """Test rfindcr with both start and end parameters."""
        s = L('abc123xyz456')
        # Find last digit in first group
        self.assertEqual(s.rfindcr(48, 58, 0, 9), 5)
        # Find last digit in second group
        self.assertEqual(s.rfindcr(48, 58, 9, 12), 11)

    def test_invert_false(self):
        """Test rfindcr with invert=False (default behavior)."""
        s = L('ABC123')
        # Find last character IN range
        self.assertEqual(s.rfindcr(65, 91, invert=False), 2)  # 'C'
        self.assertEqual(s.rfindcr(48, 58, invert=False), 5)  # '3'

    def test_invert_true(self):
        """Test rfindcr with invert=True (find NOT in range)."""
        s = L('ABC123')
        # Find last character NOT in A-Z range
        self.assertEqual(s.rfindcr(65, 91, invert=True), 5)  # '3'
        # Find last character NOT in 0-9 range
        self.assertEqual(s.rfindcr(48, 58, invert=True), 2)  # 'C'

    def test_not_found(self):
        """Test rfindcr when no matching character exists."""
        s = L('abcdef')
        # No digits in string
        self.assertEqual(s.rfindcr(48, 58), -1)
        # No uppercase in string
        self.assertEqual(s.rfindcr(65, 91), -1)

    def test_empty_string(self):
        """Test rfindcr on empty string."""
        s = L('')
        self.assertEqual(s.rfindcr(65, 91), -1)
        self.assertEqual(s.rfindcr('A', 'Z'), -1)

    def test_single_char_string(self):
        """Test rfindcr on single character string."""
        s = L('A')
        self.assertEqual(s.rfindcr(65, 91), 0)  # Found
        self.assertEqual(s.rfindcr(48, 58), -1)  # Not found

    def test_unicode_ranges(self):
        """Test rfindcr with Unicode character ranges."""
        # Cyrillic: А-Я is 1040-1072, а-я is 1072-1104
        s = L('Привет')
        # Find last uppercase Cyrillic (only П)
        self.assertEqual(s.rfindcr(1040, 1072), 0)  # 'П'
        # Find last lowercase Cyrillic
        self.assertEqual(s.rfindcr(1072, 1104), 5)  # 'т'

    def test_boundary_conditions(self):
        """Test rfindcr at string boundaries."""
        s = L('ABC')
        # Match at end
        self.assertEqual(s.rfindcr(65, 91), 2)
        # Match at start
        self.assertEqual(s.rfindcr(65, 91, 0, 1), 0)
        # Start beyond valid range
        self.assertEqual(s.rfindcr(65, 91, 10), -1)

    def test_find_vs_rfind(self):
        """Test that rfindcr finds last occurrence, not first."""
        s = L('ABC123XYZ')
        # First uppercase letter
        self.assertEqual(s.findcr(65, 91), 0)  # 'A'
        # Last uppercase letter
        self.assertEqual(s.rfindcr(65, 91), 8)  # 'Z'

    def test_error_startcp_not_int_or_str(self):
        """Test error when startcp is neither int nor string."""
        s = L('test')
        with self.assertRaises(TypeError) as cm:
            s.rfindcr([65], 91)
        self.assertIn('startcp must be int or 1-char str', str(cm.exception))

    def test_error_endcp_not_int_or_str(self):
        """Test error when endcp is neither int nor string."""
        s = L('test')
        with self.assertRaises(TypeError) as cm:
            s.rfindcr(65, [91])
        self.assertIn('endcp must be int or 1-char str', str(cm.exception))

    def test_error_multichar_startcp(self):
        """Test error when startcp is multi-character string."""
        s = L('test')
        with self.assertRaises(ValueError) as cm:
            s.rfindcr('AB', 'Z')
        self.assertIn('startcp must be an int or single character string', str(cm.exception))

    def test_error_multichar_endcp(self):
        """Test error when endcp is multi-character string."""
        s = L('test')
        with self.assertRaises(ValueError) as cm:
            s.rfindcr('A', 'XYZ')
        self.assertIn('endcp must be an int or single character string', str(cm.exception))

    def test_error_negative_startcp(self):
        """Test error when startcp is negative."""
        s = L('test')
        with self.assertRaises(ValueError) as cm:
            s.rfindcr(-1, 100)
        self.assertIn('startcp must be a non-negative code point', str(cm.exception))

    def test_error_negative_endcp(self):
        """Test error when endcp is negative."""
        s = L('test')
        with self.assertRaises(ValueError) as cm:
            s.rfindcr(0, -1)
        self.assertIn('endcp must be a non-negative code point', str(cm.exception))

    def test_error_startcp_gte_endcp(self):
        """Test error when startcp >= endcp."""
        s = L('test')
        # Equal
        with self.assertRaises(ValueError) as cm:
            s.rfindcr(65, 65)
        self.assertIn('startcp must be less than endcp', str(cm.exception))
        # Greater
        with self.assertRaises(ValueError) as cm:
            s.rfindcr(91, 65)
        self.assertIn('startcp must be less than endcp', str(cm.exception))

    def test_error_invalid_start_type(self):
        """Test error when start parameter has wrong type."""
        s = L('test')
        with self.assertRaises(TypeError) as cm:
            s.rfindcr(65, 91, 'invalid')
        self.assertIn('start must be int or None', str(cm.exception))

    def test_error_invalid_end_type(self):
        """Test error when end parameter has wrong type."""
        s = L('test')
        with self.assertRaises(TypeError) as cm:
            s.rfindcr(65, 91, 0, 'invalid')
        self.assertIn('end must be int or None', str(cm.exception))


class TestFindcrRfindcrCombined(unittest.TestCase):
    """Combined tests for both findcr and rfindcr."""

    def test_symmetry(self):
        """Test that findcr and rfindcr are symmetric."""
        s = L('ABCXYZ')
        # All characters are in A-Z range
        first = s.findcr(65, 91)
        last = s.rfindcr(65, 91)
        self.assertEqual(first, 0)
        self.assertEqual(last, 5)

    def test_single_match(self):
        """Test both methods when only one match exists."""
        s = L('abc1def')
        # Only one digit
        self.assertEqual(s.findcr(48, 58), 3)
        self.assertEqual(s.rfindcr(48, 58), 3)

    def test_multiple_ranges(self):
        """Test with overlapping searches."""
        s = L('Hello, World!')
        # Find uppercase
        self.assertEqual(s.findcr(65, 91), 0)  # 'H'
        self.assertEqual(s.rfindcr(65, 91), 7)  # 'W'
        # Find lowercase
        self.assertEqual(s.findcr(97, 123), 1)  # 'e'
        self.assertEqual(s.rfindcr(97, 123), 11)  # 'd'

    def test_with_lazy_concatenation(self):
        """Test findcr/rfindcr on concatenated L strings."""
        s1 = L('ABC')
        s2 = L('123')
        s = s1 + s2
        # Find in first part
        self.assertEqual(s.findcr(65, 91), 0)  # 'A'
        # Find in second part
        self.assertEqual(s.findcr(48, 58), 3)  # '1'
        # Rfind in first part
        self.assertEqual(s.rfindcr(65, 91), 2)  # 'C'
        # Rfind in second part
        self.assertEqual(s.rfindcr(48, 58), 5)  # '3'

    def test_with_repeated_string(self):
        """Test findcr/rfindcr on repeated L strings."""
        s = L('A1') * 3  # 'A1A1A1'
        # Find first uppercase
        self.assertEqual(s.findcr(65, 91), 0)
        # Find last uppercase
        self.assertEqual(s.rfindcr(65, 91), 4)
        # Find first digit
        self.assertEqual(s.findcr(48, 58), 1)
        # Find last digit
        self.assertEqual(s.rfindcr(48, 58), 5)

    def test_with_sliced_string(self):
        """Test findcr/rfindcr on sliced L strings."""
        s = L('ABC123XYZ')[3:6]  # '123'
        # All are digits
        self.assertEqual(s.findcr(48, 58), 0)
        self.assertEqual(s.rfindcr(48, 58), 2)
        # No letters
        self.assertEqual(s.findcr(65, 91), -1)
        self.assertEqual(s.rfindcr(65, 91), -1)


class TestFindcrRfindcrMulBuffer(unittest.TestCase):
    """Test findcr/rfindcr optimization for MulBuffer (repeated strings)."""

    def test_basic_repetition(self):
        """Test basic findcr/rfindcr on repeated strings."""
        base = L('abc123XYZ')
        s = base * 10  # 90 characters
        
        # Find first uppercase letter
        self.assertEqual(s.findcr(65, 91), 6)  # 'X' in first repetition
        # Find last uppercase letter
        self.assertEqual(s.rfindcr(65, 91), 89)  # 'Z' in last repetition
        
        # Find first digit
        self.assertEqual(s.findcr(48, 58), 3)  # '1' in first repetition
        # Find last digit
        self.assertEqual(s.rfindcr(48, 58), 86)  # '3' in last repetition

    def test_large_repetition(self):
        """Test optimization with many repetitions."""
        base = L('A1')
        s = base * 1000  # 2000 characters
        
        # Should find in first occurrence
        self.assertEqual(s.findcr(65, 91), 0)  # 'A'
        self.assertEqual(s.findcr(48, 58), 1)  # '1'
        
        # Should find in last occurrence
        self.assertEqual(s.rfindcr(65, 91), 1998)  # 'A' at position 1998
        self.assertEqual(s.rfindcr(48, 58), 1999)  # '1' at position 1999

    def test_search_within_single_repetition(self):
        """Test when search range fits within one repetition."""
        base = L('abc123XYZ')
        s = base * 100
        
        # Search in second repetition [9:18)
        self.assertEqual(s.findcr(65, 91, 9, 18), 15)  # 'X'
        self.assertEqual(s.rfindcr(65, 91, 9, 18), 17)  # 'Z'
        
        # Search in middle repetition [45:54)
        self.assertEqual(s.findcr(48, 58, 45, 54), 48)  # '1'
        self.assertEqual(s.rfindcr(48, 58, 45, 54), 50)  # '3'

    def test_search_across_multiple_repetitions(self):
        """Test when search range spans multiple repetitions."""
        base = L('abc123XYZ')
        s = base * 10  # 90 characters
        
        # Search across repetitions 2-5 [9:45)
        self.assertEqual(s.findcr(65, 91, 9, 45), 15)  # First 'X'
        self.assertEqual(s.rfindcr(65, 91, 9, 45), 44)  # Last 'Z' before 45
        
        # Search across all repetitions
        self.assertEqual(s.findcr(48, 58, 0, 90), 3)  # First digit
        self.assertEqual(s.rfindcr(48, 58, 0, 90), 86)  # Last digit

    def test_optimization_with_large_range(self):
        """Test that optimization limits search to base_len."""
        base = L('xyz123')
        s = base * 100  # 600 characters
        
        # Search in huge range [0:600) should be optimized to [0:6) for findcr
        self.assertEqual(s.findcr(48, 58, 0, 600), 3)  # '1' at position 3
        
        # Search in huge range [0:600) should be optimized to [594:600) for rfindcr
        self.assertEqual(s.rfindcr(48, 58, 0, 600), 599)  # '3' at position 599

    def test_not_found_in_repetition(self):
        """Test when character is not found in repeated string."""
        base = L('abc')
        s = base * 50  # 150 characters, all lowercase
        
        # No uppercase letters
        self.assertEqual(s.findcr(65, 91), -1)
        self.assertEqual(s.rfindcr(65, 91), -1)
        
        # No digits
        self.assertEqual(s.findcr(48, 58), -1)
        self.assertEqual(s.rfindcr(48, 58), -1)

    def test_inverted_search_repetition(self):
        """Test inverted search on repeated strings."""
        base = L('ABC')
        s = base * 20  # 60 characters, all uppercase
        
        # Find first character NOT in A-Z range (none, so -1)
        self.assertEqual(s.findcr(65, 91, invert=True), -1)
        self.assertEqual(s.rfindcr(65, 91, invert=True), -1)
        
        # With mixed content
        base2 = L('A1')
        s2 = base2 * 30  # 60 characters
        
        # Find first NOT uppercase (digit)
        self.assertEqual(s2.findcr(65, 91, invert=True), 1)  # '1'
        # Find last NOT uppercase (digit)
        self.assertEqual(s2.rfindcr(65, 91, invert=True), 59)  # Last '1'

    def test_character_params_with_repetition(self):
        """Test using character parameters with repeated strings."""
        base = L('abc123XYZ')
        s = base * 50
        
        # Using character parameters
        self.assertEqual(s.findcr('A', '['), 6)
        self.assertEqual(s.rfindcr('A', '['), 449)  # 50*9-1
        
        self.assertEqual(s.findcr('0', ':'), 3)
        self.assertEqual(s.rfindcr('0', ':'), 446)  # 50*9-4

    def test_mixed_params_with_repetition(self):
        """Test mixed int/str parameters with repeated strings."""
        base = L('test123')
        s = base * 25  # 175 characters
        
        # Mix: char start, int end
        self.assertEqual(s.findcr('0', 58), 4)  # First digit
        # Mix: int start, char end
        self.assertEqual(s.findcr(48, ':'), 4)  # First digit

    def test_boundary_cases_repetition(self):
        """Test boundary cases with repeated strings."""
        base = L('A')
        s = base * 100  # 100 'A's
        
        # All characters match
        self.assertEqual(s.findcr(65, 91), 0)
        self.assertEqual(s.rfindcr(65, 91), 99)
        
        # Search at exact boundaries
        self.assertEqual(s.findcr(65, 91, 0, 1), 0)
        self.assertEqual(s.findcr(65, 91, 99, 100), 99)
        self.assertEqual(s.rfindcr(65, 91, 99, 100), 99)

    def test_empty_base_repetition(self):
        """Test with empty base string."""
        s = L('') * 100
        
        # Empty string never finds anything
        self.assertEqual(s.findcr(65, 91), -1)
        self.assertEqual(s.rfindcr(65, 91), -1)

    def test_single_repetition(self):
        """Test with single repetition (no optimization needed)."""
        base = L('abc123XYZ')
        s = base * 1  # Same as base
        
        self.assertEqual(s.findcr(65, 91), 6)  # 'X'
        self.assertEqual(s.rfindcr(65, 91), 8)  # 'Z'
        self.assertEqual(s.findcr(48, 58), 3)  # '1'
        self.assertEqual(s.rfindcr(48, 58), 5)  # '3'

    def test_zero_repetition(self):
        """Test with zero repetitions."""
        base = L('abc123')
        s = base * 0  # Empty string
        
        self.assertEqual(len(s), 0)
        self.assertEqual(s.findcr(65, 91), -1)
        self.assertEqual(s.rfindcr(65, 91), -1)

    def test_unicode_in_repetition(self):
        """Test Unicode ranges with repeated strings."""
        # Cyrillic string
        base = L('Привет')
        s = base * 20  # 120 characters
        
        # Find first uppercase Cyrillic (П)
        self.assertEqual(s.findcr(1040, 1072), 0)
        # Find last uppercase Cyrillic (П is the only one)
        result = s.rfindcr(1040, 1072)
        # П appears at positions 0, 6, 12, 18, ... (every 6 characters)
        self.assertEqual(result, 114)  # 19 * 6
        
        # Find lowercase Cyrillic
        self.assertTrue(s.findcr(1072, 1104) > 0)
        self.assertTrue(s.rfindcr(1072, 1104) > 100)

    def test_partial_range_at_start(self):
        """Test search starting in middle of first repetition."""
        base = L('abc123XYZ')
        s = base * 10
        
        # Start at position 5 (character '3')
        self.assertEqual(s.findcr(65, 91, 5), 6)  # Next is 'X'
        # Character at 5 is '3', so it's found immediately
        self.assertEqual(s.findcr(48, 58, 5), 5)  # Current position has digit

    def test_partial_range_at_end(self):
        """Test search ending in middle of last repetition."""
        base = L('abc123XYZ')
        s = base * 10  # 90 chars
        
        # End at position 85 (cuts off 'XYZ' of last repetition)
        # Positions 81-84 are 'abc1', 85 is '2'
        # Last digit before 85 is at position 84 ('1')
        self.assertEqual(s.rfindcr(48, 58, 0, 85), 84)  # '1' in 10th repetition
        # Last uppercase before 85 is at position 80 ('Z' in 9th repetition)
        self.assertEqual(s.rfindcr(65, 91, 0, 85), 80)  # 'Z' in 9th repetition

    def test_nested_operations(self):
        """Test findcr/rfindcr on result of other operations."""
        base = L('A1B2')
        s = (base * 5) + L('C3')  # Not pure MulBuffer anymore
        
        # Should still work correctly
        self.assertEqual(s.findcr(65, 91), 0)  # 'A'
        result = s.rfindcr(65, 91)
        self.assertIn(result, [20, 21, 22])  # 'C' is in there


if __name__ == '__main__':
    unittest.main()
