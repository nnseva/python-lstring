import unittest

from lstring import _lstr


def call_rfind_lstr(lobj, sub, start=None, end=None):
    # Build args for _lstr.rfind to match signature: rfind(sub, start=None, end=None)
    if start is None and end is None:
        return lobj.rfind(sub)
    if end is None:
        return lobj.rfind(sub, start)
    return lobj.rfind(sub, start, end)


class TestLStrRFind(unittest.TestCase):
    def assert_rfind_equal(self, s, sub, start=None, end=None):
        # Python str result
        if start is None and end is None:
            expected = s.rfind(sub)
        elif end is None:
            expected = s.rfind(sub, start)
        else:
            expected = s.rfind(sub, start, end)

        l = _lstr(s)
        got = call_rfind_lstr(l, sub, start, end)
        self.assertEqual(got, expected,
                         msg=f"rfind mismatch for s={s!r} sub={sub!r} start={start} end={end}: got {got} expected {expected}")

    def test_basic(self):
        s = 'ababcababc'
        self.assert_rfind_equal(s, 'ab')
        self.assert_rfind_equal(s, 'abc')
        self.assert_rfind_equal(s, 'cab')

    def test_not_found(self):
        s = 'hello world'
        self.assert_rfind_equal(s, 'z')
        self.assert_rfind_equal(s, 'worlds')

    def test_empty_substring_defaults(self):
        s = 'abcdef'
        self.assert_rfind_equal(s, '')
        # with bounds
        self.assert_rfind_equal(s, '', 0, 0)
        self.assert_rfind_equal(s, '', 0, 1)
        self.assert_rfind_equal(s, '', 2, 4)
        self.assert_rfind_equal(s, '', 6, 6)

    def test_overlap(self):
        s = 'aaa'
        self.assert_rfind_equal(s, 'aa')  # rfind should return 1

    def test_start_end_positive(self):
        s = 'abcabcabc'
        self.assert_rfind_equal(s, 'bc', 0, 5)
        self.assert_rfind_equal(s, 'bc', 2, 8)

    def test_negative_indices(self):
        s = 'abcdefabc'
        self.assert_rfind_equal(s, 'ab', -6, -1)
        self.assert_rfind_equal(s, 'abc', -9, -3)

    def test_unicode(self):
        s = 'αβγαβγ'
        self.assert_rfind_equal(s, 'β')
        self.assert_rfind_equal(s, 'αβ', 1, 5)


if __name__ == '__main__':
    unittest.main()
