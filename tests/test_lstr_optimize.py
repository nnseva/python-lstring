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

    def test_joinbuffer_recursive_optimization(self):
        """JoinBuffer.optimize() recursively optimizes child buffers.
        
        When a JoinBuffer is too large to collapse itself, but contains
        child buffers that are small enough, calling optimize() should
        collapse the children while keeping the join structure.
        """
        # First, disable auto-optimization to create lazy structures
        lstring.set_optimize_threshold(0)
        
        # Create two slices - they stay as SliceBuffers
        s1 = self.L("hello world")[0:3]  # "hel" - length 3
        s2 = self.L("foo bar baz")[0:2]  # "fo" - length 2
        
        # Verify slices are actually SliceBuffers
        r1 = repr(s1)
        r2 = repr(s2)
        self.assertIn('[', r1, "s1 should be a slice")
        self.assertIn('[', r2, "s2 should be a slice")
        
        # Create a join - it will also stay as JoinBuffer (total length 5)
        j = s1 + s2
        
        # Verify we have a join with slices in the repr
        r_before = repr(j)
        self.assertIn('+', r_before, "Should have a join")
        self.assertIn('[', r_before, "Should have slice notation in children")
        
        # Now set threshold = 4 and call optimize():
        # - Join has length 5 >= 4, won't collapse the join itself
        # - Child slices have length 3 < 4 and 2 < 4, WILL be collapsed
        lstring.set_optimize_threshold(4)
        j.optimize()
        
        # After optimization:
        # - Join should still exist (length 5 >= threshold 4)
        # - But children should be collapsed (their lengths < 4)
        r_after = repr(j)
        self.assertIn('+', r_after, "Join should still exist after optimize")
        
        # The slices should now be gone - no more '[' notation
        # Before: (L'hello world'[0:3] + L'foo bar baz'[0:2])
        # After:  (L'hel' + L'fo')
        self.assertNotIn('[', r_after, "Slice notation should be gone after optimization")
        
        # Verify the string value is still correct
        self.assertEqual(str(j), "helfo")

    def test_mulbuffer_recursive_optimization(self):
        """MulBuffer.optimize() recursively optimizes the base buffer.
        
        When a MulBuffer is too large to collapse itself, but contains
        a base buffer that is small enough, calling optimize() should
        collapse the base while keeping the mul structure.
        """
        # First, disable auto-optimization to create lazy structures
        lstring.set_optimize_threshold(0)
        
        # Create a slice that will be the base for multiplication
        s = self.L("hello world")[0:3]  # "hel" - length 3
        
        # Verify it's actually a SliceBuffer
        r_s = repr(s)
        self.assertIn('[', r_s, "s should be a slice")
        
        # Create a mul - total length will be 6 (3 * 2)
        m = s * 2
        
        # Verify we have a mul with slice inside
        r_before = repr(m)
        self.assertIn('*', r_before, "Should have a mul")
        self.assertIn('[', r_before, "Should have slice notation in base")
        
        # Now set threshold = 5 and call optimize():
        # - Mul has length 6 >= 5, won't collapse the mul itself
        # - Base slice has length 3 < 5, WILL be collapsed
        lstring.set_optimize_threshold(5)
        m.optimize()
        
        # After optimization:
        # - Mul should still exist (length 6 >= threshold 5)
        # - But base should be collapsed (length 3 < 5)
        r_after = repr(m)
        self.assertIn('*', r_after, "Mul should still exist after optimize")
        
        # The slice should now be gone - no more '[' notation
        # Before: (L'hello world'[0:3] * 2)
        # After:  (L'hel' * 2)
        self.assertNotIn('[', r_after, "Slice notation should be gone after optimization")
        
        # Verify the string value is still correct
        self.assertEqual(str(m), "helhel")

    def test_slicebuffer_recursive_optimization(self):
        """SliceBuffer.optimize() recursively optimizes the base buffer.
        
        When a SliceBuffer is too large to collapse itself, but contains
        a base buffer that is small enough, calling optimize() should
        collapse the base while keeping the slice structure.
        """
        # First, disable auto-optimization to create lazy structures
        lstring.set_optimize_threshold(0)
        
        # Create a join that will be the base for slicing
        j = self.L("abc") + self.L("def")  # "abcdef" - length 6
        
        # Verify it's actually a JoinBuffer
        r_j = repr(j)
        self.assertIn('+', r_j, "j should be a join")
        
        # Create a slice - taking first 4 characters
        sl = j[0:4]  # "abcd" - length 4
        
        # Verify we have a slice with join inside
        r_before = repr(sl)
        self.assertIn('[', r_before, "Should have slice notation")
        self.assertIn('+', r_before, "Should have join notation in base")
        
        # Now set threshold = 5 and call optimize():
        # - Slice has length 4 < 5, WILL collapse the slice itself
        # So let's use threshold = 4:
        # - Slice has length 4 >= 4, won't collapse the slice itself
        # - Base join has length 6 >= 4, won't collapse either
        # This won't demonstrate recursive optimization well.
        
        # Let's try different approach: slice of a mul
        lstring.set_optimize_threshold(0)
        
        # Create a mul
        m = self.L("ab") * 3  # "ababab" - length 6
        r_m = repr(m)
        self.assertIn('*', r_m, "m should be a mul")
        
        # Create a slice of the mul
        sl2 = m[0:4]  # "abab" - length 4
        
        # Verify we have a slice with mul inside
        r_before2 = repr(sl2)
        self.assertIn('[', r_before2, "Should have slice notation")
        self.assertIn('*', r_before2, "Should have mul notation in base")
        
        # Now set threshold = 3:
        # - Slice has length 4 >= 3, won't collapse the slice itself
        # - Base mul has length 6 >= 3, won't collapse
        # - But the base of mul (L"ab") has length 2 < 3, WILL be collapsed if it's lazy
        # However, L"ab" is already a StrBuffer, so nothing to optimize there.
        
        # Better approach: slice of join where join contains slices
        lstring.set_optimize_threshold(0)
        
        s1 = self.L("hello")[0:2]  # "he" - length 2
        s2 = self.L("world")[0:2]  # "wo" - length 2
        j2 = s1 + s2  # "hewo" - length 4
        sl3 = j2[0:3]  # "hew" - length 3
        
        # Verify structure
        r_before3 = repr(sl3)
        self.assertIn('[', r_before3, "Should have slice notation")
        self.assertIn('+', r_before3, "Should have join in base")
        # The join should also have slices inside it
        
        # Set threshold = 3:
        # - Outer slice has length 3 >= 3, won't collapse
        # - Inner join has length 4 >= 3, won't collapse
        # - But slices inside join have length 2 < 3, WILL collapse
        lstring.set_optimize_threshold(3)
        sl3.optimize()
        
        r_after3 = repr(sl3)
        self.assertIn('[', r_after3, "Slice should still exist after optimize")
        self.assertIn('+', r_after3, "Join should still exist after optimize")
        
        # The inner slices of the join should be gone
        # Before: (L'hello'[0:2] + L'world'[0:2])[0:3]
        # After:  (L'he' + L'wo')[0:3]
        # We need to check that there are no nested '[' (slice within slice)
        # This is tricky to verify with just repr, but we can count '['
        bracket_count_before = r_before3.count('[')
        bracket_count_after = r_after3.count('[')
        self.assertLess(bracket_count_after, bracket_count_before, 
                       "Should have fewer slices after optimization")
        
        # Verify the string value is still correct
        self.assertEqual(str(sl3), "hew")

if __name__ == '__main__':
    unittest.main()
