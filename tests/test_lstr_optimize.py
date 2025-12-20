import unittest

import lstring


class TestLStrOptimize(unittest.TestCase):
    """Tests for the global optimize threshold behavior.

    Verifies that `lstring.get_optimize_threshold()` / `set_optimize_threshold()`
    control whether small lazy results are automatically collapsed into
    concrete Python strings.
    """
    @classmethod
    def setUpClass(cls):
        """Cache module handles and the original optimize threshold.

        The original threshold is saved so individual tests can modify the
        process-global optimize threshold and restore it in tearDownClass.
        """
        cls.L = lstring.L
        cls._orig = lstring.get_optimize_threshold()

    @classmethod
    def tearDownClass(cls):
        """Restore the optimize threshold saved in setUpClass.

        Ensures global state is returned to the original value after the
        test class finishes running.
        """
        lstring.set_optimize_threshold(cls._orig)

    def setUp(self):
        """Reset the optimization threshold to the class default for each test."""
        lstring.set_optimize_threshold(self._orig)

    def test_default_threshold_is_int_and_nonnegative(self):
        """The default optimize threshold is a non-negative integer.

        This guards against regressions where the getter could return
        None or a non-integer value.
        """
        val = lstring.get_optimize_threshold()
        self.assertIsNotNone(val)
        self.assertIsInstance(val, int)
        self.assertGreaterEqual(val, 0)

    def assert_backed_by_join(self, obj):
        """Helper: return True if the repr indicates a JoinBuffer backing."""
        r = repr(obj)
        return '+' in r

    def assert_backed_by_mul(self, obj):
        """Helper: return True if the repr indicates a MulBuffer backing."""
        r = repr(obj)
        return '*' in r

    def assert_backed_by_slice(self, obj):
        """Helper: return True if the repr indicates a SliceBuffer backing."""
        r = repr(obj)
        return ':' in r

    def test_threshold_zero_disables_optimization(self):
        """A threshold of 0 disables automatic collapsing; lazy buffers remain."""
        lstring.set_optimize_threshold(0)
        a = self.L("foo")
        b = self.L("bar")
        j = a + b
        self.assertTrue(self.assert_backed_by_join(j))

        m = a * 3
        self.assertTrue(self.assert_backed_by_mul(m))

        s0 = self.L("012345")
        sl = s0[1:4]
        self.assertTrue(self.assert_backed_by_slice(sl))

    def test_positive_threshold_collapses_short_results(self):
        """Positive threshold causes short results (len < threshold) to collapse."""
        lstring.set_optimize_threshold(5)

        a = self.L("ab")
        b = self.L("cd")
        j = a + b
        self.assertFalse(self.assert_backed_by_join(j))

        m = a * 2
        self.assertFalse(self.assert_backed_by_mul(m))

        s0 = self.L("01234")
        sl = s0[1:4]
        self.assertFalse(self.assert_backed_by_slice(sl))

    def test_threshold_equal_to_length_does_not_collapse(self):
        """Threshold equal to the resulting length does not trigger collapse."""
        lstring.set_optimize_threshold(4)
        a = self.L("ab")
        b = self.L("cd")
        j = a + b
        self.assertTrue(self.assert_backed_by_join(j))

        m = a * 2
        self.assertTrue(self.assert_backed_by_mul(m))

        s0 = self.L("0123")
        sl = s0[0:4]
        self.assertTrue(self.assert_backed_by_slice(sl))

    def test_non_int_threshold_disables_optimization(self):
        """Passing a non-int value to set_optimize_threshold() raises TypeError."""
        with self.assertRaises(TypeError):
            lstring.set_optimize_threshold("invalid")

    def test_negative_threshold_disables_optimization(self):
        """Negative thresholds disable optimization (treat as disabled)."""
        lstring.set_optimize_threshold(-1)
        a = self.L("ab")
        b = self.L("cd")
        j = a + b
        self.assertTrue(self.assert_backed_by_join(j))

if __name__ == '__main__':
    unittest.main()
