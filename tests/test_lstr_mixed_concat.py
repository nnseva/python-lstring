import unittest
import sys
import gc

from lstring import L
import lstring


class TestLStrMixedConcat(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls._orig_thresh = lstring.get_optimize_threshold()
        # disable C-level automatic collapsing/optimization for deterministic behavior
        lstring.set_optimize_threshold(0)

    @classmethod
    def tearDownClass(cls):
        lstring.set_optimize_threshold(cls._orig_thresh)
    def test_lstr_plus_str_result(self):
        a = L('foo')
        b = 'bar'
        res = a + b
        self.assertEqual(str(res), 'foobar')
        # original operands unchanged
        self.assertEqual(str(a), 'foo')
        self.assertEqual(b, 'bar')

    def test_str_plus_lstr_result(self):
        a = L('baz')
        b = 'qux'
        res = b + a
        self.assertEqual(str(res), 'quxbaz')
        # originals unchanged
        self.assertEqual(str(a), 'baz')
        self.assertEqual(b, 'qux')

    def test_temporary_refcounts(self):
        # Ensure mixing with Python str does not alter refcounts of operands.
        # Use sys.getrefcount which returns count+1 for the passed object, so
        # we compare deltas.
        s = 'hello_ref'
        l = L('world_ref')

        before_s = sys.getrefcount(s)
        before_l = sys.getrefcount(l)

        # perform mixed concat in both orders, delete temporaries and force GC
        res1 = l + s
        del res1

        after_s = sys.getrefcount(s)
        after_l = sys.getrefcount(l)

        self.assertEqual(before_s, after_s)
        self.assertEqual(before_l, after_l)

        res2 = s + l
        del res2
        gc.collect()

        after_s = sys.getrefcount(s)
        after_l = sys.getrefcount(l)

        self.assertEqual(before_s, after_s)
        self.assertEqual(before_l, after_l)


if __name__ == '__main__':
    unittest.main()
