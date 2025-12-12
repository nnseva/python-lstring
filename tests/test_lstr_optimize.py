import unittest

import lstring


class TestLStrOptimize(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._lstr = lstring._lstr
        cls._orig = lstring.get_optimize_threshold()

    @classmethod
    def tearDownClass(cls):
        lstring.set_optimize_threshold(cls._orig)

    def setUp(self):
        # Ensure a predictable starting state for each test
        lstring.set_optimize_threshold(self._orig)

    def test_default_threshold_is_int_and_nonnegative(self):
        val = lstring.get_optimize_threshold()
        self.assertIsNotNone(val)
        self.assertIsInstance(val, int)
        self.assertGreaterEqual(val, 0)

    def assert_backed_by_join(self, obj):
        # repr for JoinBuffer includes '+' before collapse
        r = repr(obj)
        return '+' in r

    def assert_backed_by_mul(self, obj):
        r = repr(obj)
        return '*' in r

    def assert_backed_by_slice(self, obj):
        r = repr(obj)
        return ':' in r

    def test_threshold_zero_disables_optimization(self):
        lstring.set_optimize_threshold(0)
        a = self._lstr("foo")
        b = self._lstr("bar")
        j = a + b
        self.assertTrue(self.assert_backed_by_join(j))

        m = a * 3
        self.assertTrue(self.assert_backed_by_mul(m))

        s0 = self._lstr("012345")
        sl = s0[1:4]
        self.assertTrue(self.assert_backed_by_slice(sl))

    def test_positive_threshold_collapses_short_results(self):
        # set threshold to 5: results with length <5 should be collapsed
        lstring.set_optimize_threshold(5)

        a = self._lstr("ab")
        b = self._lstr("cd")
        # join length = 4 < 5 -> collapsed
        j = a + b
        self.assertFalse(self.assert_backed_by_join(j))

        # mul: "ab" * 2 -> length 4 < 5 -> collapsed
        m = a * 2
        self.assertFalse(self.assert_backed_by_mul(m))

        s0 = self._lstr("01234")
        sl = s0[1:4]  # length 3 < 5 -> collapsed
        self.assertFalse(self.assert_backed_by_slice(sl))

    def test_threshold_equal_to_length_does_not_collapse(self):
        # set threshold to 4: only len < 4 collapses, len == 4 stays lazy
        lstring.set_optimize_threshold(4)
        a = self._lstr("ab")
        b = self._lstr("cd")
        j = a + b  # length 4 == threshold -> should NOT collapse
        self.assertTrue(self.assert_backed_by_join(j))

        m = a * 2  # length 4 == threshold -> should NOT collapse
        self.assertTrue(self.assert_backed_by_mul(m))

        s0 = self._lstr("0123")
        sl = s0[0:4]  # length 4 == threshold -> should NOT collapse
        self.assertTrue(self.assert_backed_by_slice(sl))

    def test_non_int_threshold_disables_optimization(self):
        # non-int value should be treated as disabled
        with self.assertRaises(TypeError):
            lstring.set_optimize_threshold("invalid")

    def test_negative_threshold_disables_optimization(self):
        lstring.set_optimize_threshold(-1)
        a = self._lstr("ab")
        b = self._lstr("cd")
        j = a + b
        self.assertTrue(self.assert_backed_by_join(j))

if __name__ == '__main__':
    unittest.main()
