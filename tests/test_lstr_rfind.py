import unittest
import lstring


def call_rfind_lstr(lobj, sub, start=None, end=None):
    # Build args for _lstr.rfind to match signature: rfind(sub, start=None, end=None)
    if start is None and end is None:
        return lobj.rfind(sub)
    if end is None:
        return lobj.rfind(sub, start)
    return lobj.rfind(sub, start, end)


class TestLStrRFind(unittest.TestCase):
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

        # both direct _lstr
        L = lstring._lstr(s)
        Sub = lstring._lstr(sub)
        got_b = call_rfind_lstr(L, Sub, start, end)

        # sliced haystack
        Ls = lstring._lstr(s)[:]
        got_c1 = call_rfind_lstr(Ls, Sub, start, end)

        # sliced needle
        Subs = lstring._lstr(sub)[:]
        got_c2 = call_rfind_lstr(L, Subs, start, end)

        self.assertEqual(expected, got_b,
                         msg=f"rfind mismatch (both _lstr) s={s!r} sub={sub!r} start={start} end={end}")
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
