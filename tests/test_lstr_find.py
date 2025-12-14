import unittest
import lstring


class TestLStrFind(unittest.TestCase):
    """Tests for `_lstr.find` to match Python str.find semantics.

    Each test compares three scenarios:
    - all inputs are plain Python `str` and we call `str.find`
    - all inputs are `_lstr` constructed directly from strings (fast-path applies)
    - one operand (either haystack or needle) is a sliced `_lstr` (no fast-path)
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

        # case B: both _lstr constructed directly from strings
        L = lstring._lstr(s)
        Sub = lstring._lstr(sub)
        if start is None and end is None:
            got_b = L.find(Sub)
        elif end is None:
            got_b = L.find(Sub, start)
        else:
            got_b = L.find(Sub, start, end)

        # case C: one operand is a sliced _lstr (disable fast-path)
        Ls = lstring._lstr(s)[:]
        Subs = lstring._lstr(sub)[:]
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
                         msg=f"find mismatch (both _lstr) s={s!r} sub={sub!r} start={start} end={end}")
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


if __name__ == '__main__':
    unittest.main()
