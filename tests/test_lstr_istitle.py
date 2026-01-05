"""
Tests for istitle() method across all buffer types.

Includes:
- Regression tests for istitle() bug fix (consecutive lowercase handling)
- MulBuffer boundary condition tests
- All buffer type coverage
"""
import unittest
from _lstring import L
import lstring


class TestIstitleBugFix(unittest.TestCase):
    """Tests specifically targeting the istitle() bug with consecutive lowercase letters.
    
    Bug: In Buffer::istitle(), the flag previous_is_cased was not set to true
    after processing lowercase letters, causing incorrect handling of consecutive
    lowercase letters after an uppercase letter.
    
    This caused strings like "Hello" to be incorrectly identified as not titlecase.
    """
    
    @classmethod
    def setUpClass(cls):
        cls._orig_thresh = lstring.get_optimize_threshold()
        # disable C-level automatic collapsing/optimization for deterministic behavior
        lstring.set_optimize_threshold(0)

    @classmethod
    def tearDownClass(cls):
        lstring.set_optimize_threshold(cls._orig_thresh)
    
    def test_single_word_multiple_lowercase(self):
        """Multiple consecutive lowercase letters after uppercase (bug trigger)."""
        # This was failing before the fix - using SliceBuffer to test base implementation
        self.assertTrue(L("Hello")[::-1][::-1].istitle())
        self.assertEqual(L("Hello")[::-1][::-1].istitle(), "Hello".istitle())
        
        self.assertTrue(L("World")[::-1][::-1].istitle())
        self.assertEqual(L("World")[::-1][::-1].istitle(), "World".istitle())
        
        self.assertTrue(L("Python")[::-1][::-1].istitle())
        self.assertEqual(L("Python")[::-1][::-1].istitle(), "Python".istitle())
    
    def test_long_lowercase_sequence(self):
        """Long sequences of lowercase letters after uppercase."""
        self.assertTrue(L("Hellooooo")[::-1][::-1].istitle())
        self.assertEqual(L("Hellooooo")[::-1][::-1].istitle(), "Hellooooo".istitle())
        
        self.assertTrue(L("Programming")[::-1][::-1].istitle())
        self.assertEqual(L("Programming")[::-1][::-1].istitle(), "Programming".istitle())
        
        self.assertTrue(L("Abcdefghijklmnop")[::-1][::-1].istitle())
        self.assertEqual(L("Abcdefghijklmnop")[::-1][::-1].istitle(), "Abcdefghijklmnop".istitle())
    
    def test_multiple_words_multiple_lowercase(self):
        """Multiple words with consecutive lowercase letters."""
        self.assertTrue(L("Hello World")[::-1][::-1].istitle())
        self.assertEqual(L("Hello World")[::-1][::-1].istitle(), "Hello World".istitle())
        
        self.assertTrue(L("Python Programming")[::-1][::-1].istitle())
        self.assertEqual(L("Python Programming")[::-1][::-1].istitle(), "Python Programming".istitle())
        
        self.assertTrue(L("Title Case String")[::-1][::-1].istitle())
        self.assertEqual(L("Title Case String")[::-1][::-1].istitle(), "Title Case String".istitle())
    
    def test_single_letter_words(self):
        """Single letter words (edge case for the bug)."""
        self.assertTrue(L("A")[::-1][::-1].istitle())
        self.assertEqual(L("A")[::-1][::-1].istitle(), "A".istitle())
        
        self.assertTrue(L("I Am")[::-1][::-1].istitle())
        self.assertEqual(L("I Am")[::-1][::-1].istitle(), "I Am".istitle())
        
        self.assertTrue(L("A B C")[::-1][::-1].istitle())
        self.assertEqual(L("A B C")[::-1][::-1].istitle(), "A B C".istitle())
    
    def test_two_letter_words(self):
        """Two letter words (minimal case for bug)."""
        self.assertTrue(L("Hi")[::-1][::-1].istitle())
        self.assertEqual(L("Hi")[::-1][::-1].istitle(), "Hi".istitle())
        
        self.assertTrue(L("Hi There")[::-1][::-1].istitle())
        self.assertEqual(L("Hi There")[::-1][::-1].istitle(), "Hi There".istitle())
        
        self.assertTrue(L("Ab Cd Ef")[::-1][::-1].istitle())
        self.assertEqual(L("Ab Cd Ef")[::-1][::-1].istitle(), "Ab Cd Ef".istitle())
    
    def test_false_cases_consecutive_lowercase(self):
        """Cases that should return False even with consecutive lowercase."""
        # All lowercase
        self.assertFalse(L("hello")[::-1][::-1].istitle())
        self.assertEqual(L("hello")[::-1][::-1].istitle(), "hello".istitle())
        
        # Lowercase at start
        self.assertFalse(L("helloWorld")[::-1][::-1].istitle())
        self.assertEqual(L("helloWorld")[::-1][::-1].istitle(), "helloWorld".istitle())
        
        # Multiple uppercase in sequence
        self.assertFalse(L("HEllo")[::-1][::-1].istitle())
        self.assertEqual(L("HEllo")[::-1][::-1].istitle(), "HEllo".istitle())
        
        # Uppercase after lowercase
        self.assertFalse(L("heLLo")[::-1][::-1].istitle())
        self.assertEqual(L("heLLo")[::-1][::-1].istitle(), "heLLo".istitle())
    
    def test_mixed_with_numbers_and_symbols(self):
        """Titlecase with numbers and symbols mixed in."""
        # Numbers don't affect titlecase
        self.assertTrue(L("Hello123")[::-1][::-1].istitle())
        self.assertEqual(L("Hello123")[::-1][::-1].istitle(), "Hello123".istitle())
        
        # After numbers, uppercase starts new word
        self.assertTrue(L("Test1234Test")[::-1][::-1].istitle())
        self.assertEqual(L("Test1234Test")[::-1][::-1].istitle(), "Test1234Test".istitle())
        
        # Symbols reset cased state
        self.assertTrue(L("Hello-World")[::-1][::-1].istitle())
        self.assertEqual(L("Hello-World")[::-1][::-1].istitle(), "Hello-World".istitle())
        
        self.assertTrue(L("Hello_World_Test")[::-1][::-1].istitle())
        self.assertEqual(L("Hello_World_Test")[::-1][::-1].istitle(), "Hello_World_Test".istitle())
    
    def test_multiple_spaces_between_words(self):
        """Multiple spaces between titlecase words."""
        self.assertTrue(L("Hello  World")[::-1][::-1].istitle())
        self.assertEqual(L("Hello  World")[::-1][::-1].istitle(), "Hello  World".istitle())
        
        self.assertTrue(L("A   B   C")[::-1][::-1].istitle())
        self.assertEqual(L("A   B   C")[::-1][::-1].istitle(), "A   B   C".istitle())
    
    def test_leading_trailing_spaces(self):
        """Leading and trailing spaces with titlecase."""
        self.assertTrue(L(" Hello")[::-1][::-1].istitle())
        self.assertEqual(L(" Hello")[::-1][::-1].istitle(), " Hello".istitle())
        
        self.assertTrue(L("Hello ")[::-1][::-1].istitle())
        self.assertEqual(L("Hello ")[::-1][::-1].istitle(), "Hello ".istitle())
        
        self.assertTrue(L(" Hello World ")[::-1][::-1].istitle())
        self.assertEqual(L(" Hello World ")[::-1][::-1].istitle(), " Hello World ".istitle())
    
    def test_empty_and_no_cased(self):
        """Empty strings and strings with no cased characters."""
        self.assertFalse(L("x")[1:1].istitle())  # Empty slice
        self.assertEqual(L("x")[1:1].istitle(), "".istitle())
        
        self.assertFalse(L("123")[::-1][::-1].istitle())
        self.assertEqual(L("123")[::-1][::-1].istitle(), "123".istitle())
        
        self.assertFalse(L("   ")[::-1][::-1].istitle())
        self.assertEqual(L("   ")[::-1][::-1].istitle(), "   ".istitle())
        
        self.assertFalse(L("!@#")[::-1][::-1].istitle())
        self.assertEqual(L("!@#")[::-1][::-1].istitle(), "!@#".istitle())
    
    def test_unicode_titlecase(self):
        """Unicode characters in titlecase."""
        # Cyrillic
        self.assertTrue(L("Привет")[::-1][::-1].istitle())
        self.assertEqual(L("Привет")[::-1][::-1].istitle(), "Привет".istitle())
        
        self.assertTrue(L("Привет Мир")[::-1][::-1].istitle())
        self.assertEqual(L("Привет Мир")[::-1][::-1].istitle(), "Привет Мир".istitle())
        
        # Mixed scripts
        self.assertTrue(L("Hello Мир")[::-1][::-1].istitle())
        self.assertEqual(L("Hello Мир")[::-1][::-1].istitle(), "Hello Мир".istitle())
    
    def test_apostrophes_and_contractions(self):
        """Apostrophes and contractions in titlecase."""
        self.assertTrue(L("Don'T")[::-1][::-1].istitle())
        self.assertEqual(L("Don'T")[::-1][::-1].istitle(), "Don'T".istitle())
        
        self.assertTrue(L("It'S")[::-1][::-1].istitle())
        self.assertEqual(L("It'S")[::-1][::-1].istitle(), "It'S".istitle())
    
    def test_all_caps_not_title(self):
        """All caps should not be titlecase."""
        self.assertFalse(L("HELLO")[::-1][::-1].istitle())
        self.assertEqual(L("HELLO")[::-1][::-1].istitle(), "HELLO".istitle())
        
        self.assertFalse(L("HELLO WORLD")[::-1][::-1].istitle())
        self.assertEqual(L("HELLO WORLD")[::-1][::-1].istitle(), "HELLO WORLD".istitle())
    
    def test_camelcase_not_title(self):
        """CamelCase is not titlecase."""
        self.assertFalse(L("helloWorld")[::-1][::-1].istitle())
        self.assertEqual(L("helloWorld")[::-1][::-1].istitle(), "helloWorld".istitle())
        
        self.assertFalse(L("thisIsATest")[::-1][::-1].istitle())
        self.assertEqual(L("thisIsATest")[::-1][::-1].istitle(), "thisIsATest".istitle())


class TestMulBufferIstitleBoundaries(unittest.TestCase):
    """Test istitle() for MulBuffer with various boundary conditions."""
    
    @classmethod
    def setUpClass(cls):
        cls._orig_thresh = lstring.get_optimize_threshold()
        # disable C-level automatic collapsing/optimization for deterministic behavior
        lstring.set_optimize_threshold(0)

    @classmethod
    def tearDownClass(cls):
        lstring.set_optimize_threshold(cls._orig_thresh)
    
    def test_empty_repeat_zero(self):
        """Empty string (repeat_count = 0)."""
        self.assertEqual((L("Hello") * 0).istitle(), "".istitle())
    
    def test_single_repeat(self):
        """Single repetition (repeat_count = 1)."""
        self.assertEqual((L("Hello") * 1).istitle(), "Hello".istitle())
        self.assertEqual((L("Hello World") * 1).istitle(), "Hello World".istitle())
        self.assertEqual((L("HELLO") * 1).istitle(), "HELLO".istitle())
    
    def test_space_at_start(self):
        """Space at the start of base string."""
        base = " Hello"
        for count in [1, 2, 3, 10]:
            result = (L(base) * count).istitle()
            expected = (base * count).istitle()
            self.assertEqual(result, expected, 
                           f"Failed for '{base}' * {count}")
    
    def test_space_at_end(self):
        """Space at the end of base string."""
        base = "Hello "
        for count in [1, 2, 3, 10]:
            result = (L(base) * count).istitle()
            expected = (base * count).istitle()
            self.assertEqual(result, expected,
                           f"Failed for '{base}' * {count}")
    
    def test_space_in_middle(self):
        """Space in the middle of base string."""
        base = "Hello World"
        for count in [1, 2, 3, 10]:
            result = (L(base) * count).istitle()
            expected = (base * count).istitle()
            self.assertEqual(result, expected,
                           f"Failed for '{base}' * {count}")
    
    def test_uppercase_at_start(self):
        """Uppercase letter at the start."""
        base = "Hello"
        for count in [1, 2, 3, 10]:
            result = (L(base) * count).istitle()
            expected = (base * count).istitle()
            self.assertEqual(result, expected,
                           f"Failed for '{base}' * {count}")
    
    def test_uppercase_at_end(self):
        """Uppercase letter at the end."""
        base = "helloW"
        for count in [1, 2, 3, 10]:
            result = (L(base) * count).istitle()
            expected = (base * count).istitle()
            self.assertEqual(result, expected,
                           f"Failed for '{base}' * {count}")
    
    def test_uppercase_in_middle(self):
        """Uppercase letter in the middle."""
        base = "helLo"
        for count in [1, 2, 3, 10]:
            result = (L(base) * count).istitle()
            expected = (base * count).istitle()
            self.assertEqual(result, expected,
                           f"Failed for '{base}' * {count}")
    
    def test_all_uppercase(self):
        """All uppercase letters."""
        base = "HELLO"
        for count in [1, 2, 3, 10]:
            result = (L(base) * count).istitle()
            expected = (base * count).istitle()
            self.assertEqual(result, expected,
                           f"Failed for '{base}' * {count}")
    
    def test_all_lowercase(self):
        """All lowercase letters."""
        base = "hello"
        for count in [1, 2, 3, 10]:
            result = (L(base) * count).istitle()
            expected = (base * count).istitle()
            self.assertEqual(result, expected,
                           f"Failed for '{base}' * {count}")
    
    def test_boundary_violation(self):
        """Test that boundary between repetitions is checked."""
        # "Hello" is title, but "HelloHello" is not (lowercase 'o' before 'H')
        base = "Hello"
        self.assertTrue((L(base) * 1).istitle())
        self.assertFalse((L(base) * 2).istitle())
        self.assertFalse((L(base) * 3).istitle())
    
    def test_boundary_with_space(self):
        """Space at end allows next word to start with uppercase."""
        base = "Hello "
        for count in [1, 2, 3, 10]:
            result = (L(base) * count).istitle()
            expected = (base * count).istitle()
            self.assertEqual(result, expected,
                           f"Failed for '{base}' * {count}")
    
    def test_complex_patterns(self):
        """Complex patterns with mixed cases."""
        patterns = [
            "A",
            "Ab",
            "Ab ",
            " Ab",
            "A B",
            "Ab Cd",
            "Ab Cd ",
            " Ab Cd",
        ]
        for base in patterns:
            for count in [1, 2, 3, 5]:
                result = (L(base) * count).istitle()
                expected = (base * count).istitle()
                self.assertEqual(result, expected,
                               f"Failed for '{base}' * {count}")
    
    def test_no_cased_characters(self):
        """Strings with no cased characters."""
        patterns = ["123", "   ", "!@#", ""]
        for base in patterns:
            for count in [0, 1, 2, 3]:
                if count == 0:
                    result = (L("x") * 0).istitle()
                else:
                    result = (L(base) * count).istitle()
                expected = (base * count).istitle()
                self.assertEqual(result, expected,
                               f"Failed for '{base}' * {count}")
    
    def test_single_character_patterns(self):
        """Single character base strings."""
        patterns = ["A", "a", " ", "1"]
        for base in patterns:
            for count in [1, 2, 3, 10]:
                result = (L(base) * count).istitle()
                expected = (base * count).istitle()
                self.assertEqual(result, expected,
                               f"Failed for '{base}' * {count}")


class TestIstitleAllBufferTypes(unittest.TestCase):
    """Test istitle() across all buffer types to ensure consistent behavior."""
    
    @classmethod
    def setUpClass(cls):
        cls._orig_thresh = lstring.get_optimize_threshold()
        # disable C-level automatic collapsing/optimization for deterministic behavior
        lstring.set_optimize_threshold(0)

    @classmethod
    def tearDownClass(cls):
        lstring.set_optimize_threshold(cls._orig_thresh)
    
    def test_str_buffer(self):
        """StrBuffer (direct string)."""
        s = "Hello World"
        self.assertTrue(L(s).istitle())
        self.assertEqual(L(s).istitle(), s.istitle())
    
    def test_slice_buffer(self):
        """SliceBuffer (sliced string)."""
        s = "xHello Worldx"
        self.assertTrue(L(s)[1:-1].istitle())
        self.assertEqual(L(s)[1:-1].istitle(), s[1:-1].istitle())
    
    def test_join_buffer(self):
        """JoinBuffer (concatenation)."""
        result = L("Hello") + L(" World")
        self.assertTrue(result.istitle())
        self.assertEqual(result.istitle(), "Hello World".istitle())
    
    def test_mul_buffer_single(self):
        """MulBuffer with single repetition."""
        self.assertTrue((L("Hello") * 1).istitle())
        self.assertEqual((L("Hello") * 1).istitle(), ("Hello" * 1).istitle())
    
    def test_mul_buffer_multiple_with_space(self):
        """MulBuffer with multiple repetitions (space at end)."""
        self.assertTrue((L("Hello ") * 3).istitle())
        self.assertEqual((L("Hello ") * 3).istitle(), ("Hello " * 3).istitle())
    
    def test_mul_buffer_boundary_violation(self):
        """MulBuffer boundary violation (no space between repetitions)."""
        self.assertFalse((L("Hello") * 2).istitle())
        self.assertEqual((L("Hello") * 2).istitle(), ("Hello" * 2).istitle())
    
    def test_complex_combination(self):
        """Complex combination of buffer types."""
        # (L("Hello") + L(" ")) * 2 + L("World")
        result = (L("Hello") + L(" ")) * 2 + L("World")
        expected = ("Hello " * 2) + "World"
        self.assertEqual(result.istitle(), expected.istitle())


if __name__ == '__main__':
    unittest.main()
