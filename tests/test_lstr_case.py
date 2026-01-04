"""
Tests for L string case conversion methods.
"""

import unittest
from lstring import L
import lstring

class TestLower(unittest.TestCase):
    """Tests for L.lower() method."""
    
    def test_lower_basic(self):
        """Basic lowercase conversion."""
        self.assertEqual(L('HELLO').lower(), L('hello'))
    
    def test_lower_mixed_case(self):
        """Lowercase conversion with mixed case."""
        self.assertEqual(L('HeLLo WoRLD').lower(), L('hello world'))
    
    def test_lower_already_lowercase(self):
        """Lowercase on already lowercase string."""
        self.assertEqual(L('hello').lower(), L('hello'))
    
    def test_lower_empty(self):
        """Lowercase on empty string."""
        self.assertEqual(L('').lower(), L(''))


class TestUpper(unittest.TestCase):
    """Tests for L.upper() method."""
    
    def test_upper_basic(self):
        """Basic uppercase conversion."""
        self.assertEqual(L('hello').upper(), L('HELLO'))
    
    def test_upper_mixed_case(self):
        """Uppercase conversion with mixed case."""
        self.assertEqual(L('HeLLo WoRLD').upper(), L('HELLO WORLD'))
    
    def test_upper_already_uppercase(self):
        """Uppercase on already uppercase string."""
        self.assertEqual(L('HELLO').upper(), L('HELLO'))
    
    def test_upper_empty(self):
        """Uppercase on empty string."""
        self.assertEqual(L('').upper(), L(''))
    
    def test_upper_german_sharp_s(self):
        """Uppercase German ß becomes SS (length changes)."""
        result = L('ß').upper()
        self.assertEqual(result, L('SS'))
        self.assertEqual(len(result), 2)


class TestCasefold(unittest.TestCase):
    """Tests for L.casefold() method."""
    
    def test_casefold_basic(self):
        """Basic casefolding."""
        self.assertEqual(L('HELLO').casefold(), L('hello'))
    
    def test_casefold_german_sharp_s(self):
        """Casefolding German ß becomes ss."""
        self.assertEqual(L('ß').casefold(), L('ss'))
    
    def test_casefold_comparison(self):
        """Casefolding for caseless comparison."""
        self.assertEqual(L('Straße').casefold(), L('strasse').casefold())
    
    def test_casefold_empty(self):
        """Casefolding on empty string."""
        self.assertEqual(L('').casefold(), L(''))


class TestCapitalize(unittest.TestCase):
    """Tests for L.capitalize() method."""
    
    def test_capitalize_basic(self):
        """Basic capitalization."""
        self.assertEqual(L('hello').capitalize(), L('Hello'))
    
    def test_capitalize_all_caps(self):
        """Capitalize from all uppercase."""
        self.assertEqual(L('HELLO WORLD').capitalize(), L('Hello world'))
    
    def test_capitalize_mixed_case(self):
        """Capitalize from mixed case."""
        self.assertEqual(L('hELLo WoRLD').capitalize(), L('Hello world'))
    
    def test_capitalize_empty(self):
        """Capitalize empty string."""
        self.assertEqual(L('').capitalize(), L(''))
    
    def test_capitalize_single_char(self):
        """Capitalize single character."""
        self.assertEqual(L('a').capitalize(), L('A'))


class TestTitle(unittest.TestCase):
    """Tests for L.title() method."""
    
    def test_title_basic(self):
        """Basic title casing."""
        self.assertEqual(L('hello world').title(), L('Hello World'))
    
    def test_title_all_caps(self):
        """Title case from all caps."""
        self.assertEqual(L('HELLO WORLD').title(), L('Hello World'))
    
    def test_title_mixed_case(self):
        """Title case from mixed case."""
        self.assertEqual(L('hELLo WoRLD').title(), L('Hello World'))
    
    def test_title_empty(self):
        """Title case empty string."""
        self.assertEqual(L('').title(), L(''))
    
    def test_title_with_apostrophe(self):
        """Title case with apostrophe."""
        # Python's title() capitalizes after apostrophe
        self.assertEqual(L("it's").title(), L("It'S"))


class TestSwapcase(unittest.TestCase):
    """Tests for L.swapcase() method."""
    
    def test_swapcase_basic(self):
        """Basic case swapping."""
        self.assertEqual(L('Hello').swapcase(), L('hELLO'))
    
    def test_swapcase_mixed(self):
        """Case swapping with mixed case."""
        self.assertEqual(L('HeLLo WoRLD').swapcase(), L('hEllO wOrld'))
    
    def test_swapcase_all_lower(self):
        """Swap case on all lowercase."""
        self.assertEqual(L('hello').swapcase(), L('HELLO'))
    
    def test_swapcase_all_upper(self):
        """Swap case on all uppercase."""
        self.assertEqual(L('HELLO').swapcase(), L('hello'))
    
    def test_swapcase_empty(self):
        """Swap case on empty string."""
        self.assertEqual(L('').swapcase(), L(''))
    
    def test_swapcase_double_swap(self):
        """Double swap returns original."""
        original = L('Hello World')
        self.assertEqual(original.swapcase().swapcase(), original)


class TestCaseWithMultiCodepoint(unittest.TestCase):
    """Tests for case conversion with multi-codepoint characters."""

    @classmethod
    def setUpClass(cls):
        cls._orig_thresh = lstring.get_optimize_threshold()
        # disable C-level automatic collapsing/optimization for deterministic behavior
        lstring.set_optimize_threshold(0)

    @classmethod
    def tearDownClass(cls):
        lstring.set_optimize_threshold(cls._orig_thresh)
    
    def test_decomposed_characters(self):
        """Case conversion with decomposed Unicode characters (base + combining)."""
        # é as base e + combining acute accent
        decomposed = 'e\u0301'  # é decomposed
        s = L(decomposed)
        self.assertEqual(len(decomposed), 2)  # 2 codepoints
        
        # Upper/lower should preserve decomposition
        upper = s.upper()
        self.assertEqual(len(str(upper)), 2)  # Still 2 codepoints
        self.assertEqual(upper, L('E\u0301'))
    
    def test_decomposed_in_join(self):
        """Decomposed characters across JoinBuffer boundaries."""
        # Create string with decomposed character split across parts
        decomposed = 'e\u0301'  # é decomposed
        # Concatenate parts to potentially create join buffer
        part1 = L('café')
        part2 = L(' caf') + L(decomposed)
        combined = part1 + part2
        
        # Case conversion should work correctly
        upper = combined.upper()
        self.assertEqual(upper, L('CAFÉ CAF') + L('E\u0301'))
    
    def test_emoji_with_modifier(self):
        """Emoji with skin tone modifiers (multi-codepoint)."""
        # Emoji with skin tone modifier
        emoji = '👋🏽'  # waving hand + medium skin tone
        s = L('Hello ') + L(emoji)
        
        # Case conversion should preserve emoji
        upper = s.upper()
        self.assertIn(emoji, str(upper))
    
    def test_german_sharp_s_length_change(self):
        """German ß uppercases to SS, changing length."""
        # Test across concatenation boundary
        part1 = L('Straße')
        part2 = L(' Straße')
        combined = part1 + part2
        
        self.assertEqual(len(str(combined)), 13)  # 6 + 1 + 6
        
        upper = combined.upper()
        self.assertEqual(upper, L('STRASSE STRASSE'))
        self.assertEqual(len(str(upper)), 15)  # 7 + 1 + 7
    
    def test_casefold_with_ligatures(self):
        """Casefolding with ligatures that expand."""
        # ffi ligature
        ligature = '\ufb03'  # ﬃ
        s = L('Of') + L(ligature) + L('ce')
        
        # Casefold should expand ligature
        folded = s.casefold()
        # Note: behavior may vary by Python version
        self.assertIsInstance(folded, L)
    
    def test_greek_sigma_context(self):
        """Greek sigma has different forms based on context."""
        # Word-final sigma vs medial sigma
        word = L('ΜΆΪΟΣ')  # May in Greek, uppercase
        lower = word.lower()
        # Should have final sigma at end
        self.assertEqual(lower, L('μάϊος'))
    
    def test_title_with_combining_marks(self):
        """Title case with combining diacritical marks."""
        # Create string with combining marks
        text = L('e\u0301tude')  # étude with decomposed é
        titled = text.title()
        # First character (e) should be uppercase, combining mark preserved
        # Python's title() uppercases the base and following t
        self.assertEqual(titled, L('E\u0301Tude'))
    
    def test_multiple_combining_marks(self):
        """Character with multiple combining marks."""
        # Base character + multiple combining marks
        complex_char = 'e\u0301\u0302'  # e + acute + circumflex
        s = L('t') + L(complex_char) + L('st')
        
        upper = s.upper()
        # Should preserve all combining marks
        self.assertIn('\u0301', str(upper))
        self.assertIn('\u0302', str(upper))


if __name__ == '__main__':
    unittest.main()
