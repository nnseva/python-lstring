"""Tests that exercise L objects as dictionary keys and hashing behavior."""

import unittest
import lstring


class TestLStrHashMapping1(unittest.TestCase):
    """Tests validating hashing and dict-key behavior of L instances.

    Ensures that L objects with equal contents behave as equal dictionary
    keys, and that concatenation/repetition/slicing produce values usable
    as dictionary keys equivalent to their collapsed concrete strings.
    """
    @classmethod
    def setUpClass(cls):
        """Disable optimization for predictable lazy-buffer behavior."""
        cls.original_threshold = lstring.get_optimize_threshold()
        lstring.set_optimize_threshold(0)

    @classmethod
    def tearDownClass(cls):
        """Restore optimization threshold after tests."""
        lstring.set_optimize_threshold(cls.original_threshold)

    def test_equal_strings_same_key(self):
        """Two L instances with equal contents act as the same dict key."""
        a1 = lstring.L("abc")
        a2 = lstring.L("abc")
        d = {a1: 100}
        d[a2] = 200
        self.assertEqual(len(d), 1)
        self.assertEqual(d[a1], 200)

    def test_different_strings_different_keys(self):
        """Different L contents produce distinct dictionary keys."""
        a = lstring.L("abc")
        b = lstring.L("abd")
        d = {a: 1, b: 2}
        self.assertEqual(len(d), 2)
        self.assertEqual(d[a], 1)
        self.assertEqual(d[b], 2)

    def test_concat_result_as_key(self):
        """Concatenation produces a value usable as a dict key equal to the collapsed value."""
        left = lstring.L("ab")
        right = lstring.L("c")
        concat = left + right
        ref = lstring.L("abc")
        d = {concat: "concat"}
        self.assertEqual(d[ref], "concat")

    def test_repeat_result_as_key(self):
        """Repetition (multiply) yields a key equal to the equivalent concrete string."""
        rep1 = lstring.L("ab") * 2
        rep2 = lstring.L("abab")
        d = {rep1: "repeat"}
        self.assertEqual(d[rep2], "repeat")

    def test_slice_result_as_key(self):
        """Slicing produces an L usable as a dict key equal to the expected slice."""
        s1 = lstring.L("abcd")[:3]
        s2 = lstring.L("abc")
        d = {s1: "slice"}
        self.assertEqual(d[s2], "slice")

    def test_mixed_operations_as_key(self):
        """Combined operations (concat, repeat, slice) produce the expected key value."""
        mixed = (lstring.L("ab") + lstring.L("c")) * 1
        mixed = mixed[:3]
        ref = lstring.L("abc")
        d = {mixed: "mixed"}
        self.assertEqual(d[ref], "mixed")


class TestLStrHashMapping2(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Disable optimization for predictable lazy-buffer behavior."""
        cls.original_threshold = lstring.get_optimize_threshold()
        lstring.set_optimize_threshold(0)

    @classmethod
    def tearDownClass(cls):
        """Restore optimization threshold after tests."""
        lstring.set_optimize_threshold(cls.original_threshold)

    def setUp(self):
        """Create reusable L fixtures for common test cases."""
        self.a = lstring.L("abc")
        self.b = lstring.L("abc")
        self.c = lstring.L("abd")
        self.d = lstring.L("ab")
        self.e = lstring.L("abcd")

    def test_basic_hash_equality(self):
        """Equal contents produce equal hashes; different contents produce different hashes."""
        self.assertEqual(hash(self.a), hash(self.b))
        self.assertNotEqual(hash(self.a), hash(self.c))

    def test_dict_key_equality(self):
        """Assigning via an equal L key updates the same dictionary entry."""
        d = {self.a: 123}
        d[self.b] = 456
        self.assertEqual(len(d), 1)
        self.assertEqual(d[self.a], 456)

    def test_concat_keys(self):
        """Concatenation result can be used to look up an equivalent concrete key."""
        ab = self.d + lstring.L("c")
        abc = lstring.L("abc")
        d = {ab: "concat"}
        self.assertEqual(d[abc], "concat")

    def test_repeat_keys(self):
        """Repeat (multiply) results behave as expected when used as dict keys."""
        rep1 = lstring.L("ab") * 2
        rep2 = lstring.L("abab")
        d = {rep1: "repeat"}
        self.assertEqual(d[rep2], "repeat")

    def test_slice_keys(self):
        """Slice results are equal to the expected concrete string when used as keys."""
        s1 = self.e[:3]
        s2 = lstring.L("abc")
        d = {s1: "slice"}
        self.assertEqual(d[s2], "slice")

    def test_mixed_operations(self):
        """Mixed operations produce a key equal to the expected concrete string."""
        mixed = (lstring.L("ab") + lstring.L("c")) * 1
        mixed = mixed[:3]
        ref = lstring.L("abc")
        d = {mixed: "mixed"}
        self.assertEqual(d[ref], "mixed")

if __name__ == "__main__":
    unittest.main()
