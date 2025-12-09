import unittest
import lstring

class TestLStr(unittest.TestCase):

    # --- Конструктор ---
    def test_constructor_valid(self):
        s = lstring._lstr("hello")
        self.assertEqual(str(s), "hello")

    def test_constructor_invalid(self):
        with self.assertRaises(TypeError):
            lstring._lstr(123)

    # --- Конкатенация ---
    def test_concat_valid(self):
        s1 = lstring._lstr("foo")
        s2 = lstring._lstr("bar")
        s3 = s1 + s2
        self.assertIsInstance(s3, lstring._lstr)
        self.assertEqual(str(s3), "foobar")

    def test_concat_invalid(self):
        with self.assertRaises(TypeError):
            _ = lstring._lstr("foo") + "bar"

    # --- Умножение ---
    def test_mul_valid(self):
        s = lstring._lstr("ab")
        self.assertEqual(str(s * 3), "ababab")
        self.assertEqual(str(3 * s), "ababab")

    def test_mul_invalid_negative(self):
        with self.assertRaises(RuntimeError):
            _ = lstring._lstr("ab") * -1

    def test_mul_invalid_type(self):
        with self.assertRaises(TypeError):
            _ = lstring._lstr("ab") * 2.5

    # --- Срезы ---
    def test_slice_basic(self):
        s = lstring._lstr("012345")
        self.assertEqual(str(s[1:4]), "123")
        self.assertEqual(str(s[::2]), "024")
        self.assertEqual(str(s[::-1]), "543210")
        self.assertEqual(str(s[-4:-1]), "234")
        self.assertEqual(str(s[10:20]), "")

    # --- Индексация ---
    def test_indexing(self):
        s = lstring._lstr("abc")
        self.assertEqual(s[1], "b")
        self.assertEqual(s[-1], "c")
        with self.assertRaises(IndexError):
            _ = s[10]

    # --- Преобразование в str ---
    def test_str_conversion(self):
        s = lstring._lstr("xyz")
        self.assertEqual(str(s), "xyz")

    # --- Repr ---
    def test_repr_contains_value(self):
        s = lstring._lstr("abc")
        r = repr(s)
        self.assertIn("abc", r)


if __name__ == "__main__":
    unittest.main()
