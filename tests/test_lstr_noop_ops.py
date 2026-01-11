import unittest

import lstring


class TestLStrNoOpOperations(unittest.TestCase):
    def setUp(self):
        # Keep behavior predictable (avoid auto-collapsing affecting repr etc).
        self._orig = lstring.get_optimize_threshold()
        lstring.set_optimize_threshold(0)

    def tearDown(self):
        lstring.set_optimize_threshold(self._orig)

    def test_add_empty_returns_operand_identity(self):
        a = lstring.L("abc")
        empty_l = lstring.L("")

        self.assertIs(a + "", a)
        self.assertIs("" + a, a)
        self.assertIs(a + empty_l, a)

        # left empty returns right
        self.assertIs(empty_l + a, a)

        # empty + empty returns right operand
        empty2 = lstring.L("")
        self.assertIs(empty_l + empty2, empty2)

    def test_mul_zero_and_one(self):
        a = lstring.L("abc")

        self.assertIs(a * 1, a)
        self.assertIs(1 * a, a)

        z1 = a * 0
        self.assertEqual(str(z1), "")
        self.assertEqual(len(z1), 0)
        self.assertNotIn("*", repr(z1))
        self.assertIs(type(z1), type(a))

        z2 = 0 * a
        self.assertEqual(str(z2), "")
        self.assertEqual(len(z2), 0)
        self.assertNotIn("*", repr(z2))
        self.assertIs(type(z2), type(a))

    def test_mul_empty_base_is_empty(self):
        empty = lstring.L("")
        res = empty * 5
        self.assertIs(empty, res)

    def test_slice_full_returns_self_identity(self):
        a = lstring.L("abcdef")
        self.assertIs(a[:], a)
        self.assertIs(a[0:len(a):1], a)

    def test_slice_empty_is_empty(self):
        a = lstring.L("abcdef")
        s = a[2:2]
        self.assertEqual(str(s), "")
        self.assertEqual(len(s), 0)
        self.assertNotIn(":", repr(s))
        self.assertIs(type(s), type(a))


if __name__ == "__main__":
    unittest.main()
