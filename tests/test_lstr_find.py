"""
Tests for find() and rfind() methods across all buffer types.
"""
import unittest
import lstring


class TestLStrFind(unittest.TestCase):
    """Tests for `L.find` to match Python str.find semantics.

    Each test compares three scenarios:
    - all inputs are plain Python `str` and we call `str.find`
    - all inputs are `L` constructed directly from strings (fast-path applies)
    - one operand (either haystack or needle) is a sliced `L` (no fast-path)
    """

    @classmethod
    def setUpClass(cls):
        cls._orig_thresh = lstring.get_optimize_threshold()
        # disable C-level automatic collapsing/optimization for deterministic behavior
        lstring.set_optimize_threshold(0)

    @classmethod
    def tearDownClass(cls):
        lstring.set_optimize_threshold(cls._orig_thresh)

    def _check_three(self, s, sub, start=None, end=None):
        # case A: plain Python str
        if start is None and end is None:
            expected = s.find(sub)
        elif end is None:
            expected = s.find(sub, start)
        else:
            expected = s.find(sub, start, end)

        # case B: both L constructed directly from strings
        L = lstring.L(s)
        Sub = lstring.L(sub)
        if start is None and end is None:
            got_b = L.find(Sub)
        elif end is None:
            got_b = L.find(Sub, start)
        else:
            got_b = L.find(Sub, start, end)

        # case C: one operand is a sliced L (disable fast-path)
        Ls = lstring.L(s)[:]
        Subs = lstring.L(sub)[:]
        # try haystack sliced
        if start is None and end is None:
            got_c1 = Ls.find(Sub)
        elif end is None:
            got_c1 = Ls.find(Sub, start)
        else:
            got_c1 = Ls.find(Sub, start, end)
        # try needle sliced
        if start is None and end is None:
            got_c2 = L.find(Subs)
        elif end is None:
            got_c2 = L.find(Subs, start)
        else:
            got_c2 = L.find(Subs, start, end)

        self.assertEqual(expected, got_b,
                         msg=f"find mismatch (both L) s={s!r} sub={sub!r} start={start} end={end}")
        self.assertEqual(expected, got_c1,
                         msg=f"find mismatch (sliced haystack) s={s!r} sub={sub!r} start={start} end={end}")
        self.assertEqual(expected, got_c2,
                         msg=f"find mismatch (sliced needle) s={s!r} sub={sub!r} start={start} end={end}")

    def test_empty_substring_various_starts(self):
        s = '123'
        self._check_three(s, '', None, None)
        self._check_three(s, '', -1, None)
        self._check_three(s, '', None, None)
        self._check_three(s, '', 5, None)
        self._check_three(s, '', 3, None)

    def test_search_single_char(self):
        s = '123'
        self._check_three(s, '2', None, None)
        self._check_three(s, '2', -1, None)
        self._check_three(s, '2', -3, None)
        self._check_three(s, '2', -5, None)


class TestLStrRFind(unittest.TestCase):
    """Tests for `L.rfind` to match Python str.rfind semantics.
    
    Each test compares three scenarios:
    - all inputs are plain Python `str` and we call `str.rfind`
    - all inputs are `L` constructed directly from strings
    - one operand (either haystack or needle) is a sliced `L`
    """
    
    @classmethod
    def setUpClass(cls):
        cls._orig_thresh = lstring.get_optimize_threshold()
        lstring.set_optimize_threshold(0)

    @classmethod
    def tearDownClass(cls):
        lstring.set_optimize_threshold(cls._orig_thresh)

    def _check_three(self, s, sub, start=None, end=None):
        # expected from Python str
        if start is None and end is None:
            expected = s.rfind(sub)
        elif end is None:
            expected = s.rfind(sub, start)
        else:
            expected = s.rfind(sub, start, end)

        # both direct L
        S = lstring.L(s)
        Sub = lstring.L(sub)
        got_b = S.rfind(Sub, start, end)

        # sliced haystack
        Ls = lstring.L(s)[:]
        got_c1 = Ls.rfind(Sub, start, end)

        # sliced needle
        Subs = lstring.L(sub)[:]
        got_c2 = S.rfind(Subs, start, end)

        self.assertEqual(expected, got_b,
                         msg=f"rfind mismatch (both L) s={s!r} sub={sub!r} start={start} end={end}")
        self.assertEqual(expected, got_c1,
                         msg=f"rfind mismatch (sliced haystack) s={s!r} sub={sub!r} start={start} end={end}")
        self.assertEqual(expected, got_c2,
                         msg=f"rfind mismatch (sliced needle) s={s!r} sub={sub!r} start={start} end={end}")

    def test_basic(self):
        s = 'ababcababc'
        self._check_three(s, 'ab')
        self._check_three(s, 'abc')
        self._check_three(s, 'cab')

    def test_not_found(self):
        s = 'hello world'
        self._check_three(s, 'z')
        self._check_three(s, 'worlds')

    def test_empty_substring_defaults(self):
        s = 'abcdef'
        self._check_three(s, '')
        # with bounds
        self._check_three(s, '', 0, 0)
        self._check_three(s, '', 0, 1)
        self._check_three(s, '', 2, 4)
        self._check_three(s, '', 6, 6)

    def test_overlap(self):
        s = 'aaa'
        self._check_three(s, 'aa')  # rfind should return 1

    def test_start_end_positive(self):
        s = 'abcabcabc'
        self._check_three(s, 'bc', 0, 5)
        self._check_three(s, 'bc', 2, 8)

    def test_negative_indices(self):
        s = 'abcdefabc'
        self._check_three(s, 'ab', -6, -1)
        self._check_three(s, 'abc', -9, -3)

    def test_unicode(self):
        s = 'αβγαβγ'
        self._check_three(s, 'β')
        self._check_three(s, 'αβ', 1, 5)

    def test_edge_cases_start_end_and_single(self):
        # sub length == 1
        s = 'xyzxyz'
        self._check_three(s, 'x')

        # sub matches the start of the string
        s2 = 'start_middle_end'
        self._check_three(s2, 'start')

        # sub matches the end of the string
        s3 = 'hello_world'
        self._check_three(s3, 'world')


if __name__ == '__main__':
    unittest.main()
