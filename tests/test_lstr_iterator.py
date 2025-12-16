import unittest
import sys
import gc

import lstring
from lstring import _lstr


class TestLStrIterator(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._orig_thresh = lstring.get_optimize_threshold()
        # disable C-level automatic collapsing/optimization for deterministic behavior
        lstring.set_optimize_threshold(0)

    @classmethod
    def tearDownClass(cls):
        lstring.set_optimize_threshold(cls._orig_thresh)


    def test_iteration_equivalence(self):
        s = 'Hello, αβγ🌟'
        l = _lstr(s)

        # direct character-wise comparison
        chars_str = list(iter(s))
        chars_l = list(iter(l))
        self.assertEqual(chars_l, chars_str)

    def test_refcount_preserved_after_iteration(self):
        s = 'refcount_test'
        l = _lstr(s)

        before = sys.getrefcount(l)

        it = iter(l)
        # consume iterator
        list(it)

        # delete iterator and force GC
        del it
        gc.collect()

        after = sys.getrefcount(l)
        self.assertEqual(before, after, "_lstr refcount changed after iteration")

    def test_multiple_iterators(self):
        s = 'abcdef'
        l = _lstr(s)

        before = sys.getrefcount(l)

        it1 = iter(l)
        it2 = iter(l)

        # refcount should have increased by 2 for the two iterators
        middle = sys.getrefcount(l)
        self.assertEqual(middle, before + 2)

        # advance iterators interleaved
        a1 = next(it1)
        a2 = next(it2)
        self.assertEqual(a1, s[0])
        self.assertEqual(a2, s[0])

        # consume remaining and delete one iterator
        list(it1)
        del it1
        gc.collect()

        # refcount should have decreased by 1
        after_partial = sys.getrefcount(l)
        self.assertEqual(after_partial, before + 1)

        # finish the second iterator
        list(it2)
        del it2
        gc.collect()

        after = sys.getrefcount(l)
        self.assertEqual(after, before)


if __name__ == '__main__':
    unittest.main()
