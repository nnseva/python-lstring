"""
Tests for istitle() on MulBuffer with boundary conditions.
"""
import unittest
from _lstring import L


class TestMulBufferIstitleBoundaries(unittest.TestCase):
    """Test istitle() for MulBuffer with various boundary conditions."""
    
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


if __name__ == '__main__':
    unittest.main()
